#!/bin/bash
#mcp@name:          power
#mcp@description:   A simple tool to raise a number to a power
#mcp@param:         base: int | float
#mcp@param:         exponent: int | float
#mcp@return:        int | float | None

# Check if exactly two arguments are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 base exponent"
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
echo "scale=10; e(l($1)*$2)" | bc -l
exit 0