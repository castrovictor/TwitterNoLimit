# Script to handle twitter data from/to csv/txt/python
import pprint

#Save users from txt into .py file
def usersToStack(source, dest, key):
    with open(source) as file:
        stack = file.read().split('\n')
        #Pop EOF returned by read
        stack.pop()

    # Save the stack
    with open(dest, 'w') as file:
        file.write(key + " = " + pprint.pformat(stack) + '\n')

#Save users from stack to .py file. Previous information will be lost
def usersToFile(stack, dest, key):
    with open(dest, 'w') as file:
        file.write(key + " = " + pprint.pformat(stack) + '\n')
