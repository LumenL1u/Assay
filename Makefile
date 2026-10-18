PYTHON ?= python3

.PHONY: help test lint validate render check build clean

help: ## 显示可用命令
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

test: ## 运行测试
	$(PYTHON) -m unittest discover -s tests -v

lint: ## 运行 ruff 检查
	$(PYTHON) -m ruff check .

validate: ## 校验全部任务定义
	$(PYTHON) -m evalkit validate --all

render: ## 渲染全部任务提示词
	$(PYTHON) -m evalkit render --all

check: lint test validate ## 提交前检查：lint + 测试 + 任务校验
	$(PYTHON) -m evalkit render --all --check-only

build: ## 构建 Python 包
	$(PYTHON) -m build

clean: ## 清理缓存与渲染产物
	rm -rf build dist .ruff_cache
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
	rm -rf out
