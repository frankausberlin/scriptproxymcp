#!/bin/bash
#mcp@name:          add
#mcp@description:   A simple tool to add two numbers
#mcp@param:         a: int | float
#mcp@param:         b: int | float
#mcp@return:        int | float | None

# Check if exactly two arguments are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 num1 num2"
    exit 1
fi

# check if int or float
re='^-?[0-9]+([.][0-9]+)?$'
if ! [[ $1 =~ $re ]] ; then
    # "Error: First argument is not a number"
    exit 1
elif ! [[ $2 =~ $re ]] ; then
    # "Error: Second argument is not a number"
    exit 2
fi

# return
echo "$1 + $2" | bc
exit 0
