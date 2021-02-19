# format charger board output to csv
# Peter Phelan

import sys

def main(argv):
    # get filename arg
    if len(sys.argv) < 2:
        print("No filename given, exiting")
        return
    
    # check for valid file name
    fname = sys.argv[1]
    if len(fname) < 5:
        print("Filename not long enough")
        return

    # build filenames
    file_in = fname
    file_out = fname[:-4] + ".csv"
    lines = []
    header = []
    header.append("time (min)")
    header.append("temp (C)")
    header.append("voltage (mV)")
    header.append("current (mA)")
    header.append("capacity (mAh)")
    header.append("capacity (%)")
    header.append("capacity (raw)")
    header.append("state\n")
    header = ','.join(header)
    lines.append(header)

    # read log file
    with open(file_in) as f:
        for line in f.readlines():
            # check if line is status
            split_line = line.split(", ")
            if len(split_line) != 5:
                continue

            # parse line
            line_new = []
            time_and_temp = split_line[0].split(" - ")
            line_new.append(time_and_temp[0][:-4])
            line_new.append(time_and_temp[1][:-1])
            line_new.append(split_line[1][:-2])
            line_new.append(split_line[2][:-2])
            line_new.append(split_line[3][:-3])
            status = split_line[4].split(" ")            
            line_new.append(status[0][:-1])
            line_new.append(status[1][1:-1])
            line_new.append(status[2])
            line_new = ','.join(line_new)

            # add to output
            
            lines.append(line_new)

    # write to csv
    with open(file_out,"w") as f:
        f.writelines(lines)


if __name__ == "__main__":
    main(sys.argv[1:])
