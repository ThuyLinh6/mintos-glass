# MintOS Glass — build/lint/test entrypoint
#
# CHỈ dùng công cụ có sẵn (python3 stdlib). Không cần sass, meson, sudo, mạng.
# Các target cần sass sẽ tự SKIP (không fail) cho tới khi có stylesheet thật.

PYTHON  ?= python3
SASS    ?= $(shell command -v pysassc 2>/dev/null || command -v sassc 2>/dev/null || true)
SCHEME  ?= dark

.DEFAULT_GOAL := help
.PHONY: help tokens tokens-check report lint test check safety clean scss

help: ## In trợ giúp này
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'
	@echo
	@echo "  Biến: SCHEME=$(SCHEME)  PYTHON=$(PYTHON)  SASS=$(if $(SASS),$(SASS),<không có — target scss sẽ skip>)"

tokens: ## Sinh stylesheet từ design/tokens/*.json
	$(PYTHON) tools/tokens/generate.py --scheme $(SCHEME)

tokens-check: ## Không ghi; fail nếu file generated lệch token (dùng trong CI)
	$(PYTHON) tools/tokens/generate.py --scheme all --check

report: ## In toàn bộ token đã phân giải + bảng contrast
	$(PYTHON) tools/tokens/generate.py --scheme all --report

scss: ## Biên dịch SCSS -> CSS (tự skip nếu chưa có file entry hoặc thiếu compiler)
	@if [ -z "$(SASS)" ]; then echo "SKIP scss: không tìm thấy pysassc/sassc (không tự cài — xem docs/plan/08-risks.md R6)"; exit 0; fi
	@if [ ! -f src/cinnamon/cinnamon.scss ]; then echo "SKIP scss: src/cinnamon/cinnamon.scss chưa tồn tại (T04)"; exit 0; fi
	echo "TODO(T04): $(SASS) src/cinnamon/cinnamon.scss dist/MintOS-Glass/cinnamon/cinnamon.css"

safety: ## Quét tooling tìm chuỗi cấm (/usr, sudo, apt, dpkg)
	$(PYTHON) tools/lint/safety_paths.py

lint: tokens-check safety ## tokens-check + safety-paths

test: ## Chạy test Tầng 1 (offline, stdlib unittest)
	$(PYTHON) -m unittest discover -s tests -t . 

check: lint test ## everything — cổng CI chính
	@echo "OK — make check xanh"

clean: ## Xoá file generated (token sẽ được sinh lại)
	rm -f src/cinnamon/tokens/_tokens.scss src/gtk-3.0/sass/_tokens.scss \
	      src/gtk-4.0/sass/_tokens.scss src/libadwaita/tokens.css \
	      docs/design-system/tokens.md design/tokens.lock.json
	find . -path ./.git -prune -o -name '__pycache__' -type d -print0 | xargs -0 rm -rf
