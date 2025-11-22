import tkinter

from components.browser import Browser

if __name__ == '__main__':
    import sys

    Browser().load(sys.argv[1])
    tkinter.mainloop()
