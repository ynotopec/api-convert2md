.PHONY: install run

install:
	./install.sh

run:
	./run.sh $${HOST:-0.0.0.0} $${PORT:-8088}
