import json
import subprocess
import numpy
import matplotlib.pyplot as plot
from matplotlib.backends import backend_pdf


def run_ping(hostnames, num_packets, raw_ping_output_filename, aggregated_ping_output_filename):
	num_pings = num_packets + 1
	raw_ping_output = {}
	agg_ping_output = {}
	counter = 0
	for hostname in hostnames:
		counter += 1
		print("On hostname #" + str(counter) + ": " + hostname)
		ping_command = "ping -c " + str(num_pings) + " " + hostname
		ping_output = ""
		try:
			ping_output = subprocess.check_output(ping_command, shell=True)
		except subprocess.CalledProcessError as err:
			ping_output = err.output

		hostname_rtts, hostname_stats = parse_hostname_ping_output(ping_output, num_packets)
		raw_ping_output[hostname] = hostname_rtts
		agg_ping_output[hostname] = hostname_stats

	raw_ping_json = json.dumps(raw_ping_output)
	agg_ping_json = json.dumps(agg_ping_output)

	print("done json")
	
	# print(raw_ping_json)
	with open(raw_ping_output_filename, "w+") as f:
		f.write(raw_ping_json)
	print("done write raw")
	
	# print(agg_ping_json)
	with open(aggregated_ping_output_filename, "w+") as f:
		f.write(agg_ping_json)
	print("done write agg")
	


		
# returns (raw_output, agg_output )
def parse_hostname_ping_output(output, num_packets):
	output_tokens = output.split("\n")
	if output_tokens[0].startswith("PING"):
		output_tokens = output_tokens[1:]

	all_failed = True
	hostname_rtts = []
	hostname_median_rtts = []
	drop_counter = 0
	ping_counter = 0
	for tok in output_tokens:
		if ping_counter == num_packets:
			break
		if tok.startswith("Request timeout for icmp_seq"):
			# timeout ping
			hostname_rtts.append(float(-1.0))
			ping_counter += 1
			drop_counter += 1
		elif tok == "":
			pass
		elif "time=" in tok and "ttl=" in tok:
			# normal ping
			all_failed = False
			start = tok.index("time=") + 5
			end = tok.index(" ms")
			time = float(tok[start:end])
			hostname_rtts.append(time)
			hostname_median_rtts.append(time)
			ping_counter += 1

	diff = len(hostname_rtts) - num_packets
	if diff > 0:
		for x in range(diff):
			hostname_rtts.append(-1.0)
	# hostname_rtts = hostname_rtts[:num_packets]

	hostname_stats = None
	if all_failed:
		hostname_stats = { "drop_rate" : float(100.0) , "max_rtt" : float(-1.0), "median_rtt" : float(-1.0)}
	else:
		adv_stats = output_tokens[-2]
		basic_stats = output_tokens[-3]
		drop_rate = drop_counter / float(ping_counter)
		median_rtt = numpy.median(hostname_median_rtts)
		max_rtt = max(hostname_median_rtts)
		hostname_stats = { "drop_rate" : drop_rate , "max_rtt" : max_rtt, "median_rtt" : median_rtt}

	return (hostname_rtts, hostname_stats)


def read_in_names_from_file(filename):
	# Takes in a file with host names on each line and return a list
	host_names = []
	with open(filename, "r") as f:
		host_names = [ln.strip('\n') for ln in f.readlines()]
	return host_names



def plot_ping_cdf(raw_ping_results_filename, output_cdf_filename):
	with open(raw_ping_results_filename, 'r') as content_file:
		content = content_file.read()
	pings_data = json.loads(content)
	rtt_list_unfilt = None
	hostname = None
	for key in pings_data.keys():
		hostname = key
		rtt_list_unfilt = pings_data[key]

		rtt_list = [x for x in rtt_list_unfilt if x != -1.0]
		rtt_list.sort()

		x_vals = []
		y_vals = []
		counter = 1
		total = len(rtt_list)
		for rtt in rtt_list:
			x_vals.append(rtt)
			y_vals.append(counter / float(total))
			counter += 1
		plotlabel = key + " RTT CDF"
		plot.step(x_vals, y_vals, label=plotlabel)
	plot.legend() # This shows the legend on the plot.
	plot.grid() # Show grid lines, which makes the plot easier to read.
	plot.xlabel("Ms") # Label the x-axis.
	plot.ylabel("Cumulative Fraction") # Label the y-axis.
	# plot.show()

 	with backend_pdf.PdfPages(output_cdf_filename) as pdf:
 		pdf.savefig()
 	plot.clf()



def plot_median_rtt_cdf(agg_ping_results_filename, output_cdf_filename):
	with open(agg_ping_results_filename, 'r') as content_file:
		content = content_file.read()
	agg_data = json.loads(content)

	median_rtts_unfilt = []
	for key in agg_data.keys():
		median_rtts_unfilt.append(agg_data[key]["median_rtt"])
	median_rtts = [x for x in median_rtts_unfilt if x != -1.0]

	median_rtts.sort()
	
	x_vals = []
	y_vals = []
	counter = 1
	total = len(median_rtts)
	for rtt in median_rtts:
		x_vals.append(rtt)
		y_vals.append(counter / float(total))
		counter += 1
	
	plot.step(x_vals, y_vals, label="Median RTT CDF")
	plot.legend() # This shows the legend on the plot.
	plot.grid() # Show grid lines, which makes the plot easier to read.
	plot.xlabel("Ms") # Label the x-axis.
	plot.ylabel("Cumulative Fraction") # Label the y-axis.
	# plot.show()

 	with backend_pdf.PdfPages(output_cdf_filename) as pdf:
 		pdf.savefig()
 	plot.clf()



plot_ping_cdf("rtt_b_raw.json", "ping_rtt_b_cdf.pdf")

# ping_list = read_in_names_from_file("alexa_top_100")
# run_ping(ping_list, 10, "rtt_a_raw.json", "rtt_a_agg.json")

# run_ping(["google.com", "todayhumor.co.kr", "zanvarsity.ac.tz", "taobao.com"], 500, "rtt_b_raw.json", "rtt_b_agg.json")


# run_ping(["google.com", "youtube.com", "baidu.com"], 15, "TESTTEST_RTT.json", "TESTTEST_AGG.json")
# plot_ping_cdf("TESTTEST_RTT.json", "TESTTEST.pdf")

# run_ping(["google.com"], 25, "GOOGLE_RTT.json", "GOOGLE_AGG.json")
# plot_ping_cdf("GOOGLE_RTT.json", "GOOGLE_RTT_CDF.pdf")


#plot_median_rtt_cdf("AGG_OUTPUT_TEST.txt", "MEDIAN_RTT_CDF.pdf")

# plot_median_rtt_cdf("rtt_a_agg.json", "median_rtt_a_cdf.pdf")