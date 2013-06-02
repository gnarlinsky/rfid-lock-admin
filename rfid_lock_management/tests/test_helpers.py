from termcolor import colored

# should we print messages describing the tests as they run?
PRINT_INFO = True

def t_info(mess_str, level=1):
    """
    Print message to screen related to what is currently being tested. If
    PRINT_INFO is False, these still serve as documentation for the associated
    lines. Takes a string with the message and level, which refers to the type
    of message, and formats the string with color and indentation accordingly.
    The higher the level number, the more verbose/specific. 

    Types of messages:
    - level 1: TestCase name (white on green, prepend new line)
    - level 2: test method name and docstring (green, no indentation)
    - level 3: action description (cyan, no indentation)
    - level 4: assertion description (blue, indent one)
    - level 5: closer assertion description (magenta, indent two)
    """
    if PRINT_INFO:
        if level == 1:
            print colored("\n" + mess_str, "white", "on_green")
        elif level == 2:
            print colored(mess_str, "green")
        elif level == 3:
            print colored(mess_str, "cyan")
        elif level == 4:
            print colored("\t" + mess_str, "blue")
        elif level == 5:
            print colored("\t\t" + mess_str, "magenta")
