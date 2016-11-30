
import subprocess
import json
from utils import *
import sets
import matplotlib.pyplot as plot
from matplotlib.backends import backend_pdf


def read_in_names_from_file(filename):
	# Takes in a file with host names on each line and return a list
	host_names = []
	with open(filename, "r") as f:
		host_names = [ln.strip('\n') for ln in f.readlines()]
	return host_names


def run_dig(hostname_filename, output_filename, dns_query_server=None):
	hostnames = read_in_names_from_file(hostname_filename)
	dig_results_list = []

	if dns_query_server:
		# only dig to that dns server
		for hostname in hostnames:
			print(hostname)
			for i in range(5): 	# changeto 5
				dig_command = "dig " + hostname + " @" + dns_query_server
				dig_output = ""
				try:
					dig_output = subprocess.check_output(dig_command, shell=True)
				except subprocess.CalledProcessError as err:
					dig_output = err.output

				dig_results_list.append(generate_dict_from_spef_dig_output(dig_output, hostname))

	else:
		for hostname in hostnames:
			print(hostname)
			for i in range(5):
				dig_command = "dig +trace +tries=1 +nofail " + hostname
				dig_output = ""
				try:
					dig_output = subprocess.check_output(dig_command, shell=True)
				except subprocess.CalledProcessError as err:
					dig_output = err.output

				dig_results_list.append(generate_dict_from_reg_dig_output(dig_output, hostname))

	digs_json = json.dumps(dig_results_list)
	with open(output_filename, "w+") as f:
		f.write(digs_json)



def generate_dict_from_spef_dig_output(lines, hostname):
	lines = lines.split("\n")
	answer_lines = []
	success = False
	for line in lines:
		if line.startswith(";; AUTHORITY SECTION:"):
			success = True
		if line.startswith(";; Query time: "):
			time_millis = line[15:-5]
		elif line == "" or line.startswith(";"):
			pass
		else:
			answer_lines.append(line)
	answers_list, unused_success = parse_query_answers(answer_lines, hostname)
	if success and time_millis:
		queries_list = [{TIME_KEY: time_millis, ANSWERS_KEY: answers_list}]
		dig_dict = {NAME_KEY : hostname, SUCCESS_KEY : success, QUERIES_KEY : queries_list}	
	else:
		dig_dict = {NAME_KEY : hostname, SUCCESS_KEY : success}	
	return dig_dict


# generate one dig dict; going to get called 500 times
def generate_dict_from_reg_dig_output(lines, hostname):
	lines = lines.split("\n")
	section_end_indices = []
	for line_num in range(len(lines)):
		if ";; Received" in lines[line_num] and "bytes from " in lines[line_num]:
			section_end_indices.append(line_num)

	queries_list = []
	for i in range(len(section_end_indices)):
		# print(lines[section_end_indices[i]])
		line = lines[section_end_indices[i]]
		time_millis = line[line.index(" in ") + 4: -3]
		if i == 0:
			answers_list, success = parse_query_answers(lines[3:section_end_indices[i]], hostname)
		else:
			answers_list, success = parse_query_answers(lines[section_end_indices[i-1] + 2:section_end_indices[i]], hostname)
		query_dict = {TIME_KEY: time_millis, ANSWERS_KEY: answers_list}
		queries_list.append(query_dict)
	
	if success:
		dig_dict = {NAME_KEY : hostname, SUCCESS_KEY : success, QUERIES_KEY : queries_list}	
	else:
		dig_dict = {NAME_KEY : hostname, SUCCESS_KEY : success}
	return dig_dict

		


# returns list of dicts, and success or not
def parse_query_answers(lines, hostname):
	answers = []
	last_line = None
	for line in lines:
		# print(line)
		line_toks = [x for x in line.split("\t") if x!=""]
		answer_dict = {QUERIED_NAME_KEY: line_toks[0], TTL_KEY : 0, TYPE_KEY : None, ANSWER_DATA_KEY : None}
		try:
			answer_dict = {QUERIED_NAME_KEY: line_toks[0], TTL_KEY : line_toks[1], TYPE_KEY : line_toks[3], ANSWER_DATA_KEY : line_toks[4]}
		except IndexError as e:
			new_line_toks = []
			for line in line_toks:
				new_line_toks += line.split(" ")
			answer_dict = {QUERIED_NAME_KEY: new_line_toks[0], TTL_KEY : new_line_toks[1], TYPE_KEY : new_line_toks[3], ANSWER_DATA_KEY : new_line_toks[4]}
		answers.append(answer_dict)
		last_line = line
	if last_line and last_line.startswith(hostname):
		success = True
	else:
		success = False
	return answers, success



def get_average_ttls(filename):
	root_server_list = []
	tld_server_dict = {}
	ns_dict = {}
	terminating_dict = {}

	with open(filename, 'r') as content_file:
		content = content_file.read()

	dig_runs_list = json.loads(content)

	# Format of file: list of JSON dictionaries
	# Go dict by dict, and then query by query

	# PART 1: Gather TTLS
	for dig_run in dig_runs_list: # Each of these is a dictionary
		if not dig_run[SUCCESS_KEY]:
			pass
		else:
			name = dig_run[NAME_KEY]
			queries = dig_run[QUERIES_KEY] # List
			for q in queries:
				queried_name = q[ANSWERS_KEY][0][QUERIED_NAME_KEY]

				# Determine type of query
				if queried_name == ".":
					ttls = [int(answer[TTL_KEY])/1000.0 for answer in q[ANSWERS_KEY]] # Get list of TTLs for this query, guaranteed to be all NS records
					root_server_list = root_server_list + ttls
				elif queried_name.count(".") == 1:
					ttls = [int(answer[TTL_KEY])/1000.0 for answer in q[ANSWERS_KEY]] # Get list of TTLs for this query, guaranteed to be all NS records
					if queried_name in tld_server_dict.keys():
						tld_server_dict[queried_name] = tld_server_dict[queried_name] + ttls
					else:
						tld_server_dict[queried_name] = ttls
				elif queried_name[:-1] == name:

					# Records may be mixed NS/other, must go answer by answer to add TTLs to right buckets
					for answer in q[ANSWERS_KEY]:

						# CNAME or A Record
						if answer[TYPE_KEY] in ("CNAME", "A"):
							#print("Found final record: " + queried_name + " :" + str(int(answer[TTL_KEY])/1000.0))
							if queried_name in terminating_dict.keys():
								terminating_dict[queried_name].append(int(answer[TTL_KEY])/1000.0)
							else:
								terminating_dict[queried_name] = [int(answer[TTL_KEY])/1000.0]

						# NS record, just happens to be for original query
						else:
							#print("Found NS/CNAME record: " + queried_name + " :" + str(int(answer[TTL_KEY])/1000.0))
							if queried_name in ns_dict.keys():
								ns_dict[queried_name].append(int(answer[TTL_KEY])/1000.0)
							else:
								ns_dict[queried_name] = [int(answer[TTL_KEY])/1000.0]
				else:
					#print("Found NS/CNAME records: " + queried_name + " :" + str([int(answer[TTL_KEY])/1000.0 for answer in q[ANSWERS_KEY]]))

					ttls = [int(answer[TTL_KEY])/1000.0 for answer in q[ANSWERS_KEY]] # Get list of TTLs for this query, guaranteed to be all NS records
					if queried_name in ns_dict.keys():
						ns_dict[queried_name] = ns_dict[queried_name] + ttls
					else:
						ns_dict[queried_name] = ttls

	# PART 2: Condense TTLS
	tld_server_list = []
	for tld_key in tld_server_dict.keys():
		tld_server_list.append(sum(tld_server_dict[tld_key])/float(len(tld_server_dict[tld_key])))

	ns_list = []
	for ns_key in ns_dict.keys():
		ns_list.append(sum(ns_dict[ns_key])/float(len(ns_dict[ns_key])))

	terminating_list = []
	for terminating_key in terminating_dict.keys():
		terminating_list.append(sum(terminating_dict[terminating_key])/float(len(terminating_dict[terminating_key])))

	# Part 3: Average out over all
	average_root_ttl = sum(root_server_list)/float(len(root_server_list))
	average_TLD_ttl = sum(tld_server_list)/float(len(tld_server_list))
	average_ns_ttl = sum(ns_list)/float(len(ns_list))
	average_terminating_ttl = sum(terminating_list)/float(len(terminating_list))

	#print([average_root_ttl, average_TLD_ttl, average_ns_ttl, average_terminating_ttl])
	return [average_root_ttl, average_TLD_ttl, average_ns_ttl, average_terminating_ttl]



def get_average_times(filename):
	with open(filename, 'r') as content_file:
		digs_json = content_file.read()
	digs_list = json.loads(digs_json)

	total_sites_count = 0
	total_sites_time = 0
	total_final_request_count = 0
	total_final_request_time = 0
	for dig_dict in digs_list:
		if dig_dict[SUCCESS_KEY]:
			total_sites_count += 1
			for query in dig_dict[QUERIES_KEY]:
				total_sites_time += int(query[TIME_KEY])
				for answer in query[ANSWERS_KEY]:
					if answer[TYPE_KEY] == "A" or answer[TYPE_KEY] == "CNAME":
						total_final_request_count += 1
						total_final_request_time += int(query[TIME_KEY])
	average_resolve_time = total_sites_time / float(total_sites_count)
	average_final_request_time = total_final_request_time / float(total_final_request_count)
	return [average_resolve_time, average_final_request_time]



def generate_time_cdfs(json_filename, output_filename):
	with open(json_filename, 'r') as content_file:
		digs_json = content_file.read()
	digs_list = json.loads(digs_json)

	site_resolution_times = []
	final_request_times = []
	for dig_dict in digs_list:
		if dig_dict[SUCCESS_KEY]:
			resolution_time = 0
			for query in dig_dict[QUERIES_KEY]:
				resolution_time += int(query[TIME_KEY])
				for answer in query[ANSWERS_KEY]:
					if answer[TYPE_KEY] == "A" or answer[TYPE_KEY] == "CNAME":
						final_request_times.append(int(query[TIME_KEY]))
						break
			site_resolution_times.append(resolution_time)

	site_resolution_times.sort()
	final_request_times.sort()
	y1 = []
	for i in range(len(site_resolution_times)):
		y1.append(i/float(len(site_resolution_times)))
	y2 = []
	for i in range(len(final_request_times)):
		y2.append(i/float(len(final_request_times)))

	plot.step(site_resolution_times, y1, label="Total Resolution Time")
	plot.step(final_request_times, y2, label="Final Request Time")
	plot.legend() # This shows the legend on the plot.
	plot.grid() # Show grid lines, which makes the plot easier to read.
	plot.xlabel("Ms") # Label the x-axis.
	plot.ylabel("Cumulative Fraction") # Label the y-axis.
	# plot.show()
	with backend_pdf.PdfPages(output_filename) as pdf:
 		pdf.savefig()
 	plot.clf()


# generate_time_cdfs("part3_submit/dns_output_1.json", "testtest.pdf")







def count_different_dns_responses(filename1, filename2):
	with open(filename1, 'r') as content_file:
		digs_json = content_file.read()
	digs_list1 = json.loads(digs_json)
	with open(filename2, 'r') as content_file:
		digs_json = content_file.read()
	digs_list2 = json.loads(digs_json)

	# print("italian: " + str(len(digs_list1)))
	# print("original: " + str(len(digs_list2)))
	# counter = 0
	# for dig in digs_list1:
	# 	if counter % 5 == 0:
	# 		print("")
	# 	print(dig[NAME_KEY])
	# 	counter += 1

	changed_ip_count_1_file = 0
	changed_ip_count_2_file = 0
	for i in range(0, len(digs_list1), 5):
		host_unique_ips = sets.Set()
		for j in range(5):
			one_dig_resp = sets.Set()
			dig_dict = digs_list1[i+j]
			if dig_dict[SUCCESS_KEY]:
				for query in dig_dict[QUERIES_KEY]:
					for answer in query[ANSWERS_KEY]:
						if answer[TYPE_KEY] == "A" or answer[TYPE_KEY] == "CNAME":
							one_dig_resp.add(answer[ANSWER_DATA_KEY])
			if one_dig_resp != sets.Set():
				host_unique_ips.add(one_dig_resp)
		# print("")
		# print(len(host_unique_ips))
		if len(host_unique_ips) > 1:
			changed_ip_count_1_file += 1
		for j in range(5):
			one_dig_resp = sets.Set()
			dig_dict = digs_list2[i+j]
			if dig_dict[SUCCESS_KEY]:
				for query in dig_dict[QUERIES_KEY]:
					for answer in query[ANSWERS_KEY]:
						if answer[TYPE_KEY] == "A" or answer[TYPE_KEY] == "CNAME":
							one_dig_resp.add(answer[ANSWER_DATA_KEY])
			if one_dig_resp != sets.Set():
				host_unique_ips.add(one_dig_resp)
		# print(len(host_unique_ips))
		if len(host_unique_ips) > 1:
			print(host_unique_ips)
			changed_ip_count_2_file += 1

	return[changed_ip_count_1_file, changed_ip_count_2_file]
	# print("\n")
	# print(changed_ip_count_1_file)
	# print(changed_ip_count_2_file)


# get_average_ttls("alexa_goog_wiki_digs.json")
# print(count_different_dns_responses("part3_submit/dns_output_1.json", "part3_submit/dns_output_2.json"))
# count_different_dns_responses("part3_submit/dns_output_1.json", "alexa_100_digs.json")

# print(get_average_times("alexa_5_digs.json"))
# print(get_average_times("part3_submit/dns_output_1.json"))

# run_dig("alexa_top_100", "alexa_100_digs.json", None)
# run_dig("alexa_top_100", "alexa_100_digs.json", "i.root-servers.net")
# run_dig("alexa_top_100", "alexa_100_digs.json", "a.ns.facebook.com")


# run_dig("alexa_top_100", "dns_output_other_server.json", "ip-44-209.sn1.clouditalia.com")
# print(count_different_dns_responses("dns_output_other_server.json", "part3_submit/dns_output_1.json"))





