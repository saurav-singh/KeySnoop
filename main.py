from snoop import mainTap
from recordKey import recordKey

def main():

	print ("1) Train")
	print ("2) Start")
	print ("3) Record Surface")
	print ("4) Record Keys")
	ch = input("Enter your option")
	
	if(ch == 1):
		print("here")
		mainTap('A')
	elif(ch == 2):
		mainTap('C')
	elif(ch == 3):
		mainTap('B')
	elif(ch == 4):
		recordKey()
	else:
		print ("Wrong input")

mainTap('A')
print('\n\n\n\nStart')
mainTap('C')
