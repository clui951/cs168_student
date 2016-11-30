import subprocess
import json
import time

def run_traceroute(hostnames, num_packets, output_filename):
	all_traceroute_output = ""
	for hostname in hostnames:
		traceroute_command = "traceroute -a -q " + str(num_packets) + " " + hostname
		traceroute_output = ""
		try:
			traceroute_output = subprocess.check_output(traceroute_command, shell=True)
			# p = subprocess.Popen(['traceroute', '-a', '-q', '5', 'google.com'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			# traceroute_output, err = p.communicate()
		except subprocess.CalledProcessError as err:
			traceroute_output = err.output
		all_traceroute_output += "traceroute to " + hostname + "\n"
		all_traceroute_output += traceroute_output
		all_traceroute_output += "\n"

	with open(output_filename, "w+") as f:
		f.write(all_traceroute_output)


# run_traceroute(["google.com", "facebook.com", "www.berkeley.edu", "allspice.lcs.mit.edu", "todayhumor.co.kr", "www.city.kobe.lg.jp", "www.vutbr.cz", "zanvarsity.ac.tz"], 5, "tr_a1.txt")
# run_traceroute(["google.com", "facebook.com", "www.berkeley.edu", "allspice.lcs.mit.edu", "todayhumor.co.kr", "www.city.kobe.lg.jp", "www.vutbr.cz", "zanvarsity.ac.tz"], 5, "tr_a2.txt")
# run_traceroute(["google.com", "facebook.com", "www.berkeley.edu", "allspice.lcs.mit.edu", "todayhumor.co.kr", "www.city.kobe.lg.jp", "www.vutbr.cz", "zanvarsity.ac.tz"], 5, "tr_a3.txt")
# run_traceroute(["google.com", "facebook.com", "www.berkeley.edu", "allspice.lcs.mit.edu", "todayhumor.co.kr", "www.city.kobe.lg.jp", "www.vutbr.cz", "zanvarsity.ac.tz"], 5, "tr_a4.txt")
run_traceroute(["google.com", "facebook.com", "www.berkeley.edu", "allspice.lcs.mit.edu", "todayhumor.co.kr", "www.city.kobe.lg.jp", "www.vutbr.cz", "zanvarsity.ac.tz"], 5, "tr_a5.txt")


#part b
# run_traceroute(["tpr-route-server.saix.net", "route-server.ip-plus.net", "route-views.oregon-ix.net", "route-views.on.bb.telus.com"], 5, "tr_b1.txt")




def parse_traceroute(raw_traceroute_filename, output_filename):
	with open(raw_traceroute_filename, 'r') as content_file:
		content = content_file.read()
	lines = content.split("\n")
	start_indices = []
	for line_num in range(len(lines)):
		# print(line)
		if lines[line_num].startswith("traceroute to"):
			start_indices.append(line_num)

	all_traceroutes_dict = {}
	all_traceroutes_dict["timestamp"] = str(time.time())
	for i in range(len(start_indices)):
		if i == len(start_indices) - 1:
			start = start_indices[i]
			hostname, hostname_trace_list = parse_single_traceroute(lines[start:])
		else:
			start = start_indices[i]
			end = start_indices[i+1] - 1
			hostname, hostname_trace_list = parse_single_traceroute(lines[start:end])
		all_traceroutes_dict[hostname] = hostname_trace_list

	all_traceroutes_json = json.dumps(all_traceroutes_dict)
	# print(all_traceroutes_json)
	with open(output_filename, "w+") as f:
		f.write(all_traceroutes_json)



# returns hostname and list of lists of routers
def parse_single_traceroute(lines):
	current_hop = -1
	hostname = None
	hop_list = [] #[ [{},{},{},  [{}, {}  ]
	hop_set = []
	for line in lines:
		hop_dict = {}
		if line.startswith("traceroute to "):
			hostname = line[14:].split(" ")[0]
			continue

		if "[AS" in line and "]" in line:
			if not line.startswith("    "):
				# new hop distance
				current_hop += 1
				hop_set = []
				hop_list.append([])

			ASN = line[line.index("[AS") + 3 : line.index("]")]
			
			line = line[line.index("]") + 2 : ]
			line_tok = line.split(" ")
			name = line_tok[0]
			ip = line_tok[1].strip("(").strip(")")

			if ip in hop_set:
				continue
			else:
				hop_set.append(ip)

			# Insert into dictionary and place in overall list
			hop_dict["name"] = name
			hop_dict["ip"] = ip
			hop_dict["ASN"] = ASN
			hop_list[current_hop].append(hop_dict)

		elif line:
			# all *****
			current_hop += 1
			hop_set = []
			hop_list.append([])
			hop_dict["name"] = "None"
			hop_dict["ip"] = "None"
			hop_dict["ASN"] = "None"
			hop_list[current_hop].append(hop_dict)

	return hostname, hop_list







# parse_traceroute("TRACEROUTE_TEST.txt", "ASDFASDFASDFADS.txt")
# parse_traceroute("examples/traceroute_sample.txt", "ASDFGHJKLKJHGFDSASDFGHJK.txt")



# parse_traceroute("tr_a1.txt", "tr_a1.json")
# parse_traceroute("tr_a2.txt", "tr_a2.json")
# parse_traceroute("tr_a3.txt", "tr_a3.json")
# parse_traceroute("tr_a4.txt", "tr_a4.json")
parse_traceroute("tr_a5.txt", "tr_a5.json")


# part b
# parse_traceroute("tr_b1.txt", "tr_b1.json")







