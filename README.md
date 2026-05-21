# LLM Machine

OpenCode-style 로컬 LLM 개발 IDE. Electron + Monaco Editor 기반 GUI와 Python Agent 시스템으로 구성됩니다.

## 아키텍처

```
[Electron Frontend]          [Python Backend]           [Ollama]
┌─────────────────┐         ┌──────────────────┐      ┌─────────┐
│ Monaco Editor    │  HTTP   │ Flask API Server │ HTTP │ Local   │
│ File Explorer    │◄───────►│ Agent Orchestrator│◄────►│ LLM     │
│ Chat Panel       │ REST    │ Tool Layer       │      │ Model   │
│ Diff Viewer      │         │ Planner/Loop     │      └─────────┘
└─────────────────┘         └──────────────────┘
```

## 설치 및 실행

### 사전 요구사항

- Python 3.10+
- Node.js 18+
- [Ollama](https://ollama.ai) 설치 및 실행
- LLM 모델 다운로드: `ollama pull llama3.2`

### 빠른 실행

```bash
./start.sh
```

### 수동 실행

```bash
# 1. Python 가상환경
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Electron 의존성
cd frontend && npm install && cd ..

# 3. Backend 실행
source venv/bin/activate
python backend/server.py &

# 4. Frontend 실행
cd frontend && npx electron .
```

## 기능

- **Monaco Editor**: VS Code와 동일한 에디터 (구문 강조, 자동 완성, 미니맵)
- **AI 채팅**: 자연어로 코드 작성, 수정, 버그 수정 지시
- **파일 탐색기**: 프로젝트 파일 트리 뷰
- **Diff 뷰어**: 변경 사항 확인
- **설정**: 모델 변경, Ollama 호스트 설정

## 사용 예시

```
>>> Create a Python Flask hello world app
>>> Fix the bug in src/main.py
>>> Refactor utils.py to use async/await
>>> Run pytest and fix failures
```

## 프로젝트 구조

```
llm_machine/
├── backend/
│   └── server.py          # Flask API server
├── frontend/
│   ├── main.js            # Electron main process
│   ├── preload.js          # Context bridge
│   ├── package.json
│   └── src/
│       ├── index.html      # Main window
│       ├── styles.css      # Dark theme UI
│       ├── renderer.js     # Main renderer
│       └── ui/
│           ├── chat.js     # Chat panel
│           ├── fileExplorer.js
│           └── diffViewer.js
├── src/                    # Python backend core
│   ├── main.py
│   ├── models/schemas.py
│   ├── backend/
│   │   ├── orchestrator.py
│   │   ├── planner.py
│   │   ├── agent_loop.py
│   │   ├── tools/ (filesystem, shell, git, search)
│   │   └── interface/ (ollama)
├── start.sh               # Launch script
└── requirements.txt
```
