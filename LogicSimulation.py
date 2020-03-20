import sys
import tkinter as tk
from tkinter import filedialog
import time
import threading as thr
import queue

Window = tk.Tk()
Window.withdraw()

#try get files from command line
try:
	target_bench, target_pattern = sys.argv[1], sys.argv[2]
except:
	target_bench, target_pattern = "", ""
# get .bench
while target_bench == "":
	print("please select the bench file.")
	target_bench = filedialog.askopenfilename(initialdir = ".", 
	title = "Choose Bench file", 
	filetypes=(("Bench files", "*.bench"), ("All files", "*.*")))

tStart1 = time.time()
#bench processing
inputlist = [] # to input data in right order
outputlist = [] # to output data in right order
gatelist = {} # stores every gate: {key=gatename, value=object in gateclass}
valuelist = {} # stores ever value by input or by gate output

class and_gate():
	def __init__(self, inputs):
		self.inputs = inputs
	def computeValue(self, default_in=valuelist):
		unknown = False
		for i in self.inputs:
			value = default_in[i]
			if value == None:
				return None
			elif value == "0":
				return "0"
			elif value == "u":
				unknown = True
			elif value == "1":
				continue
			else:
				raise ValueError
		if unknown == True:
			return "u"
		else:
			return "1"
class nand_gate():
	def __init__(self, inputs):
		self.inputs = inputs
	def computeValue(self, default_in=valuelist):
		unknown = False
		for i in self.inputs:
			value = default_in[i]
			if value == None:
				return None
			elif value == "0":
				return "1"
			elif value == "u":
				unknown = True
			elif value == "1":
				continue
			else:
				raise ValueError
		if unknown == True:
			return "u"
		else:
			return "0"
class or_gate():
	def __init__(self, inputs):
		self.inputs = inputs
	def computeValue(self, default_in=valuelist):
		unknown = False
		for i in self.inputs:
			value = default_in[i]
			if value == None:
				return None
			elif value == "1":
				return "1"
			elif value == "u":
				unknown = True
			elif value == "0":
				continue
			else:
				raise ValueError
		if unknown == True:
			return "u"
		else:
			return "0"
class nor_gate():
	def __init__(self, inputs):
		self.inputs = inputs
	def computeValue(self, default_in=valuelist):
		unknown = False
		for i in self.inputs:
			value = default_in[i]
			if value == None:
				return None
			elif value == "1":
				return "0"
			elif value == "u":
				unknown = True
			elif value == "0":
				continue
			else:
				raise ValueError
		if unknown == True:
			return "u"
		else:
			return "1"
class xor_gate():
	def __init__(self, inputs):
		self.inputs = inputs
	def computeValue(self, default_in=valuelist):
		amount_1 = 0
		for i in self.inputs:
			value = default_in[i]
			if value == None:
				return None
			elif value == "1":
				amount_1 += 1
			elif value == "u":
				return "u"
			elif value == "0":
				continue
			else:
				raise ValueError
		if amount_1 % 2 == 0:
			return "0"
		else:
			return "1"
class buf_gate():
	def __init__(self, inputs):
		self.inputs = inputs
	def computeValue(self, default_in=valuelist):
		if len(self.inputs)>=2:
			raise ValueError("buffer only support 1 input!")
		return default_in[self.inputs[0]]
class not_gate():
	def __init__(self, inputs):
		self.inputs = inputs
	def computeValue(self, default_in=valuelist):
		if len(self.inputs) > 1:
			raise ValueError("inverter only support 1 input!")
		value = default_in[self.inputs[0]]
		if value == "1":
			return "0"
		if value == "0":
			return "1"
		if value == "u":
			return "u"
		if value == None:
			return None
		raise ValueError

class queueTerminator(thr.Thread):
	def __init__(self, queue, *a, **b):
		super().__init__(*a, **b)
		self.queue = queue
	def run(self):
		while self.queue.qsize()>0:
			Job_pat(self.queue.get())

# bench file : read and store bench
file_bench = open(target_bench)
print("reading the file...")
for line in file_bench:
	if line.startswith('#') or line.strip().lower() == "":
		continue
	elif line.lower().startswith('input'):
		pin_name = line[6:-2].strip()
		inputlist.append(pin_name)
		valuelist[pin_name] = None
	elif line.lower().startswith('pinput'):
		pin_name = line[7:-2].strip()
		inputlist.append(pin_name)
		valuelist[pin_name] = None
	elif line.lower().startswith('output'):
		pin_name = line[7:-2].strip()
		outputlist.append(pin_name)
	elif line.lower().startswith('poutput'):
		pin_name = line[8:-2].strip()
		outputlist.append(pin_name)
	else:
		line_2 = line.split("=")
		pin_name = line_2[0].strip()
		line_3 = line_2[1].strip(") \n").split("(")
		gate_type = line_3[0].strip().lower()
		gate_input_str = line_3[1]
		gate_input_list = gate_input_str.split(",")
		for i in range(len(gate_input_list)):
			gate_input_list[i] = gate_input_list[i].strip()
		if gate_type == "and":
			gatelist[pin_name] = and_gate(gate_input_list)
		elif gate_type == "nand":
			gatelist[pin_name] = nand_gate(gate_input_list)
		elif gate_type == "or":
			gatelist[pin_name] = or_gate(gate_input_list)
		elif gate_type == "nor":
			gatelist[pin_name] = nor_gate(gate_input_list)
		elif gate_type == "xor":
			gatelist[pin_name] = xor_gate(gate_input_list)
		elif gate_type == "buff" or gate_type == "buf":
			gatelist[pin_name] = buf_gate(gate_input_list)
		elif gate_type == "not":
			gatelist[pin_name] = not_gate(gate_input_list)
		else:
			raise ValueError
		valuelist[pin_name] = None
file_bench.close()

# sort gate order
gate_sorted_onlyname = []
gate_amount = len(gatelist)
valuelist_result = dict.copy(valuelist)
for i in range(len(inputlist)):
	key = inputlist[i]
	valuelist_result[key] = "u"
finish_value = 0
while finish_value != len(gatelist):
	for gatename in gatelist:
		if valuelist_result[gatename] == None:
			for k in gatelist[gatename].inputs:
				if valuelist_result[k] == None:
					valuelist_result[gatename] = None
					break
				else:
					valuelist_result[gatename] = "u"
			if valuelist_result[gatename] == "u":
				finish_value += 1
				gate_sorted_onlyname.append(gatename)
	process = finish_value / len(gatelist) * 100
	block = int(process/2)
	bar = "sorting gate: [" + "■"*block + " "*(50-block) + "] %.2f " % process + "%\r"
	sys.stdout.write(bar)
print()
tEnd1 = time.time()
print("bench running time of %s =" %(target_bench.split("/")[-1]), tEnd1-tStart1)

# get .pat for input
while target_pattern == "":
	print("please select the pattern file.")
	target_pattern = filedialog.askopenfilename(initialdir = target_bench + "/..", 
	title = "Choose Pattern file for " + target_bench.split("/")[-1], 
	filetypes=(("Pattern files", "*.pat"), ("All files", "*.*")))

target_result = target_pattern.split("/")[-1].split(".")[0]+".result"
file_result = open(target_result, "w")

tStart2 = time.time()
# pattern file : read and compute the pattern and print it out.
def Job_pat(pat_line):
	# global orderCount
	pattern = pat_line.strip().split(": ")
	pattern_No = int(pattern[0].strip())
	pattern_inputs = pattern[1]
	valuelist_result = dict.copy(valuelist)
	for i in range(len(inputlist)):
		key = inputlist[i]
		valuelist_result[key] = pattern_inputs[i]
	for gatename in gate_sorted_onlyname:
		valuelist_result[gatename] = gatelist[gatename].computeValue(valuelist_result)
		if valuelist_result[gatename] == None:
			print(gatename)
			file_result.write(gatename+"\n")
			raise ValueError
	answer=""
	for i in outputlist:
		answer += valuelist_result[i]
	# while pattern_No != orderCount:
	# 	pass
	print(pattern_No, ":", answer)
	file_result.write(str(pattern_No) + ":" + str(answer) + "\n")
	# orderCount+=1
myqueue = queue.Queue()
myThreads = []
# orderCount = 0
file_pat = open(target_pattern)
print("reading the file...")
for line in file_pat:
	if line.startswith('#') or line.startswith('*') or line.strip().lower() == "":
		continue
	myqueue.put(line)
for i in range(30):
	myThreads.append(queueTerminator(queue=myqueue))
	myThreads[i].start()
while myqueue.qsize()>0:
			Job_pat(myqueue.get())
for i in range(6):
	myThreads[i].join()
tEnd2 = time.time()
print("Running time of %s =" %(target_pattern.split("/")[-1]), tEnd1-tStart1+tEnd2-tStart2)