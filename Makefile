DESTDIR = /usr/local/bin

PROGRAM = aws-ssh

install: $(PROGRAM).py
	cp $(PROGRAM).py $(DESTDIR)/$(PROGRAM)
	chmod +x $(DESTDIR)/$(PROGRAM)

uninstall:
	rm -f $(DESTDIR)/$(PROGRAM)