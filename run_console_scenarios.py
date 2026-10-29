"""Replay this project's documented console scenarios with visible input and output."""
from __future__ import annotations

import argparse
import codecs
from dataclasses import dataclass
import os
from pathlib import Path
import re
import selectors
import shlex
import signal
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parent
PROMPTS = (
    '날짜(YYYY-MM-DD): ', '타입(income/expense): ', '카테고리: ',
    '금액(양수 정수): ', '메모(선택): ', '태그(쉼표 구분, 선택): ',
)


@dataclass
class Scenario:
    command: str
    expected_code: int
    answers: list[tuple[str, str]]
    id_label: str | None
    line: int
    title: str


def scenario_title(command: str, heading: str, screen: str, code: int) -> str:
    """Describe the operation briefly using its command and documented context."""
    words = shlex.split(command)
    if '-m' in words and 'budget_app' in words:
        args = words[words.index('budget_app') + 1:]
        if args[:1] == ['--data-dir']:
            args = args[2:]
        if '--help' in args:
            return ' '.join(args[:-1]) + ' 도움말' if len(args) > 1 else '전체 도움말'
        action = args[0]
        if action == 'add':
            return f'{heading} 입력 거부' if code else f'{heading} 추가'
        if action == 'category':
            operation = {'add': '추가', 'list': '목록', 'remove': '삭제'}[args[1]]
            if '중복 카테고리' in screen:
                return '중복 카테고리 거부'
            if '카테고리명을 입력하세요' in screen:
                return '빈 카테고리명 거부'
            if '사용 중인 카테고리' in screen:
                return '사용 중 카테고리 삭제 차단'
            return f'카테고리 {operation}'
        if code:
            for clue, title in [
                ('없는 데이터', '없는 거래 ID 거부'),
                ('수정할 필드', '수정 필드 누락 거부'),
                ('손상된 JSONL', '손상 파일 오류 안내'),
                ('필수 헤더', 'CSV 필수 헤더 누락'),
                ('No such file', '없는 CSV 파일 오류'),
                ('저장 파일을 덮어쓸', '저장 파일 덮어쓰기 차단'),
                ('조건을 입력하세요', '내보내기 조건 누락'),
                ('월과 기간', '월·기간 동시 지정 거부'),
                ('늦을 수 없습니다', '역순 기간 거부'),
                ('skipped=', 'CSV 오류 행 건너뛰기'),
            ]:
                if clue in screen:
                    return title
            return {'update': '잘못된 금액 수정', 'summary': '잘못된 월 조회',
                    'list': '잘못된 출력 개수', 'budget': '잘못된 예산 금액',
                    'delete': '삭제 ID 누락'}.get(action, f'{action} 오류 검증')
        if action == 'list':
            return '출력 건수 제한' if '--limit' in args else '거래 목록 조회'
        if action == 'search':
            if '데이터 없음' in screen:
                return '검색 결과 없음 확인'
            return '복합 조건 검색' if '--category' in args else (
                '태그 검색' if '--tag' in args else '기간 검색')
        if action == 'summary':
            if '데이터 없음' in screen:
                return '빈 월 요약 확인'
            if '[경고]' in screen:
                return '예산 초과 경고 확인'
            return '예산 사용률 확인' if '사용률' in screen else '월별 합계·TOP 확인'
        if action == 'update' and "--memo '' --tags ''" in command:
            return '메모·태그 비우기'
        if action == 'export':
            if '(0 records)' in screen:
                return '빈 CSV 내보내기'
            return '월별 CSV 내보내기' if '--month' in args else '기간 CSV 내보내기'
        return {'search': '조건별 거래 검색', 'summary': '월별 요약 조회',
                'budget': '월 예산 설정', 'update': '거래 수정',
                'delete': '거래 삭제', 'import': 'CSV 가져오기',
                'export': 'CSV 내보내기'}[action]
    if 'unittest' in words:
        return '전체 자동 테스트'
    if words[0] == 'cat':
        return '검증 CSV 파일 생성' if '<<' in command else '저장 파일 내용 확인'
    return {'ls': '저장 파일 생성 확인', 'cp': '원본 비교용 복사',
            'cmp': '실패 후 원본 보존 확인', 'mkdir': '손상 파일 준비'}.get(words[0], heading)


def read_scenarios(document: str) -> list[Scenario]:
    """Read shell blocks and their following input examples/exit codes in order."""
    blocks = list(re.finditer(r'^```sh\n(.*?)^```[ \t]*$', document, re.M | re.S))
    scenarios = []
    for index, block in enumerate(blocks):
        end = blocks[index + 1].start() if index + 1 < len(blocks) else len(document)
        explanation = document[block.end():end]
        expected = re.search(r'^```text\n(.*?)^```', explanation, re.M | re.S)
        screen = expected[1] if expected else ''
        status = re.search(r'종료 코드: `(\d+)`', explanation)
        command = block[1].strip()
        answers = []
        if re.search(r'\bcategory (add|remove)$', command):
            prompts = ('카테고리명: ',)
        elif re.search(r'\bbudget_app\b.*\badd$', command):
            prompts = PROMPTS
        else:
            prompts = ()
        # Consume prompts in order so add's category listing is not an input field.
        position = 0
        for prompt in prompts:
            match = re.search(r'^' + re.escape(prompt) + r'([^\n]*)$', screen[position:], re.M)
            if not match:
                raise ValueError(f'입력 예시를 찾을 수 없습니다: {command} / {prompt}')
            answers.append((prompt, match[1]))
            position += match.end()
        label = re.search(r'\[저장 완료\] id=(TX-[A-F])\b', screen)
        # Run each help invocation separately to check every exit code.
        commands = command.splitlines() if all(
            line.startswith('python3.12 ') for line in command.splitlines()
        ) else [command]
        for item in commands:
            headings = re.findall(r'^#{2,3} (.+)$', document[:block.start()], re.M)
            heading = re.sub(r'^\d+\.\s*', '', headings[-1]) if headings else '콘솔 검증'
            code = int(status[1]) if status else 0
            scenarios.append(Scenario(item, code,
                                      answers, label[1] if label else None,
                                      document.count('\n', 0, block.start()) + 1,
                                      scenario_title(item, heading, screen, code)))
    if not scenarios:
        raise ValueError('문서에서 실행할 sh 코드 블록을 찾지 못했습니다.')
    return scenarios


class Transcript:
    """Send the same decoded text immediately to the console and a UTF-8 log."""
    def __init__(self, stream):
        self.stream = stream

    def write(self, text: str) -> None:
        sys.stdout.write(text)
        sys.stdout.flush()
        self.stream.write(text)
        self.stream.flush()


def execute(command: str, answers: list[tuple[str, str]], transcript: Transcript,
            timeout: float) -> tuple[int, str]:
    """Stream actual merged output; send and echo each answer when prompted."""
    environment = dict(os.environ, PYTHONUNBUFFERED='1', PYTHONIOENCODING='utf-8')
    process = subprocess.Popen(
        ['/bin/bash', '-e', '-o', 'pipefail', '-c', command], cwd=ROOT,
        env=environment, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, start_new_session=True,
    )
    decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')
    captured = ''
    answer_index = 0
    scan_position = 0
    deadline = time.monotonic() + timeout
    try:
        if not answers:
            process.stdin.close()
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            while selector.get_map():
                if time.monotonic() >= deadline:
                    raise TimeoutError(f'명령 실행 제한 시간 {timeout:g}초를 초과했습니다.')
                for key, _ in selector.select(timeout=0.1):
                    chunk = os.read(key.fd, 65536)
                    text = decoder.decode(chunk, final=not chunk)
                    captured += text
                    transcript.write(text)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    if answer_index < len(answers):
                        prompt, answer = answers[answer_index]
                        # A prompt is at a line start; the add category listing
                        # cannot match because scanning starts after the type input.
                        match = re.search(r'(?:^|\n)' + re.escape(prompt), captured[scan_position:])
                        if match:
                            scan_position += match.end()
                            process.stdin.write((answer + '\n').encode('utf-8'))
                            process.stdin.flush()
                            transcript.write(answer + '\n')
                            captured += answer + '\n'
                            scan_position = len(captured)
                            answer_index += 1
                            if answer_index == len(answers):
                                process.stdin.close()
        code = process.wait(timeout=max(0.1, deadline - time.monotonic()))
        if answer_index != len(answers):
            raise RuntimeError('예상한 대화형 질문이 모두 출력되지 않았습니다.')
        return code, captured
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        process.stdout.close()
        if not process.stdin.closed:
            process.stdin.close()


def main() -> int:
    parser = argparse.ArgumentParser(description='CONSOLE_SCENARIOS.md를 입력/출력 표시와 함께 자동 실행')
    parser.add_argument('--timeout', type=float, default=60,
                        help='각 명령의 제한 시간(초), 기본 60')
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error('--timeout은 0보다 커야 합니다.')
    scenarios = read_scenarios((ROOT / 'CONSOLE_SCENARIOS.md').read_text(encoding='utf-8'))
    run_directory = Path(tempfile.mkdtemp(prefix='budget-console-run-'))
    data_directory = run_directory / 'console-test'
    log_path = run_directory / 'transcript.log'
    identifiers: dict[str, str] = {}
    with log_path.open('w', encoding='utf-8') as log:
        transcript = Transcript(log)
        transcript.write(f'실행 데이터: {data_directory}\n전체 입출력 로그: {log_path}\n'
                         f'실행할 명령 블록: {len(scenarios)}개\n')
        try:
            for index, scenario in enumerate(scenarios, 1):
                command = scenario.command.replace('./console-test', shlex.quote(str(data_directory)))
                command = command.replace('python3.12 ', shlex.quote(sys.executable) + ' ')
                for label in re.findall(r'\bTX-[A-F]\b', command):
                    if label not in identifiers:
                        raise ValueError(f'{label}의 실제 거래 ID를 아직 얻지 못했습니다.')
                    command = command.replace(label, identifiers[label])
                transcript.write(f'\n[{index}/{len(scenarios)}] {scenario.title} '
                                 f'| 문서 {scenario.line}행\n$ {command}\n')
                code, output = execute(command, scenario.answers, transcript, args.timeout)
                if output and not output.endswith('\n'):
                    transcript.write('\n')
                transcript.write(f'[종료 코드] 실제={code}, 예상={scenario.expected_code}\n')
                if code != scenario.expected_code:
                    raise RuntimeError('예상 종료 코드와 달라 실행을 중단합니다.')
                if scenario.id_label:
                    match = re.search(r'\[저장 완료\] id=(TX-[0-9a-f]{32})', output)
                    if not match:
                        raise RuntimeError('거래 저장 결과에서 실제 ID를 찾지 못했습니다.')
                    identifiers[scenario.id_label] = match[1]
            transcript.write(f'\n[완료] {len(scenarios)}개 명령 블록의 예상 종료 코드 확인 완료.\n'
                             f'전체 기록: {log_path}\n'
                             '화면 출력은 실제 실행 결과이며, 문서의 예상 화면과 자동 문자열 비교는 하지 않습니다.\n')
            return 0
        except KeyboardInterrupt:
            transcript.write('\n[중단] 사용자가 실행을 취소했습니다.\n')
            return 130
        except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.TimeoutExpired) as error:
            transcript.write(f'\n[실패] {error}\n기록: {log_path}\n')
            return 1


if __name__ == '__main__':
    raise SystemExit(main())
