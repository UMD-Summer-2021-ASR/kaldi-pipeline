import argparse
from decimal import Decimal

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_ctm",
                       default=None, help="input ctm.")
    parser.add_argument("-o", "--output_vtt",
                       default=None, help="output vtt.")

    args = parser.parse_args()
    with open(args.input_ctm, 'r') as f1, open(args.output_vtt, 'w') as f2:
        lines = f1.readlines()
        f2.write("WEBVTT Kind: captions; Language: en\n\n")
        for line in lines:
            vals = line.split()
            start = vals[2]
            end = Decimal(start) + Decimal(vals[3])
            txt = vals[4]
            f2.write("00:{} --> 00:{}\n{}\n\n".format(start,end,txt))
if __name__ == "__main__":
    main()