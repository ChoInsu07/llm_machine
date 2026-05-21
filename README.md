# LLM Machine

OpenCode-style 로컬 LLM 개발 IDE 시스템. Ollama를 통해 로컬 LLM을 구동하여 코드 작성, 파일 편집, 명령 실행 등을 자동화하는 Agent 시스템입니다.

## 아키텍처

```
User → CLI(Frontend) → Agent Orchestrator(Backend) → Agent Loop + Tools → Ollama Interface → LLM Model
```

## 설치 및 실행

### 사전 요구사항

- Python 3.10+
- [Ollama](https://ollama.ai) 설치 및 실행
- LLM 모델 다운로드: `ollama pull llama3.2`

### 설치

```bash
pip install -r requirements.txt
```

### 실행

```bash
python src/main.py
```

### 설정

`.env.example`을 `.env`로 복사하여 설정하거나, `llm_machine.json` 파일을 프로젝트 루트에 생성:

```json
{
  "model": "qwen2.5",
  "ollama_host": "http://localhost:11434"
}
```

## 사용법

CLI에서 명령을 자연어로 입력하면 Agent가 자동으로:

1. **Plan** - 작업 계획 수립
2. **Action** - 파일 읽기/쓰기, 명령 실행, 검색 등 수행
3. **Observation** - 결과 관찰
4. **Retry** - 실패 시 재시도

### 명령어

- `/plan` - Planning 모드 토글
- `/status` - 시스템 상태 확인
- `/help` - 도움말

## 예시

```
>>> Create a Python script that prints "Hello, LLM World!"
>>> Search for all TODO comments in the project
>>> Run tests and fix failures
```

## 프로젝트 구조

```
src/
├── main.py                    # Entry point
├── models/schemas.py          # Data models
├── frontend/cli.py            # CLI interface
└── backend/
    ├── orchestrator.py        # Agent orchestrator
    ├── planner.py             # Plan generation
    ├── agent_loop.py          # Plan → Action → Observation → Retry
    ├── tools/
    │   ├── filesystem.py      # File read/write/edit
    │   ├── shell.py           # Command execution
    │   ├── git_tool.py        # Git operations
    │   └── search.py          # Code search
    └── interface/
        ├── base.py            # Base LLM interface
        └── ollama.py          # Ollama API client
```
