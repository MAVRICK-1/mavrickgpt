.PHONY: docs

check:
	poetry run pre-commit run -a


test-llm-ask-mavrick:
	poetry run pytest tests/llm/test_ask_mavrick.py -n 6 -vv

test-without-llm:
	poetry run pytest tests -m "not llm"