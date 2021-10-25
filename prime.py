import math
import random
# print(2)
for num in range(3,101,2):
    if all(num%i!=0 for i in range(3,int(math.sqrt(num))+1, 2)):
        values = (num)
        print(random.shuffle(values))
