import readline

words = ["apple", "app", "apricot", "banana", "bat", "ball"]

def completer(text, state):
    matches = [w for w in words if w.startswith(text)]
    if state < len(matches):
        return matches[state]
    return None

readline.set_completer(completer)
readline.parse_and_bind("tab: complete")

user_input = input("Type something (press TAB): ")
print("You selected:", user_input)
