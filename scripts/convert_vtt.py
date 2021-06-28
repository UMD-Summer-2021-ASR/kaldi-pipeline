import argparse
from decimal import Decimal
from typing import Dict, List, Set
import os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_ctm",
                       default=None, help="input ctm.")
    parser.add_argument("-r","--rttm",
                        default=None,help="input rttm")
    parser.add_argument("-o", "--output_vtt",
                       default=None, help="output vtt.")
    args = parser.parse_args()
    print(args.rttm)
    os.makedirs(args.output_vtt, exist_ok=True)
    with open(args.input_ctm, 'r') as f1, open(args.rttm,'r') as rt:
        lines = f1.readlines()
        rttm = rt.readlines()
        process(lines=lines,rttm=rttm,dir=args.output_vtt)

def process(lines:List[str], rttm:List[str], dir):
    speaker: Dict[str,Dict[str,List]] = dict()
    files : Set[str]= set()
    for l in rttm:
        [_,file,_,start,dur,_,_,id,_,_] = l.split()
        files.add(file)
        speaker.setdefault(file,{"rttm":[],"sub":[]})
        speaker[file]["rttm"].append([id,start,dur])
    for l in lines:
        [file,_,start,dur,word] = l.split()
        speaker[file]["sub"].append([word,start,dur])
    for file in files:
        with open(dir + "/" + file+".vtt","w") as f:
            f.write("WEBVTT Kind: captions; Language: en\n\n")
            for line in speaker[file]["sub"]:
                spk = 1
                for sp in speaker[file]["rttm"]:
                    if float(sp[1]) <= float(line[1]):
                        spk = sp[0]
                f.write("00:{} --> 00:{}\n<v Speaker {}>{}\n\n".format(line[1],Decimal(line[1]) + Decimal(line[2]),spk,line[0]))

if __name__ == "__main__":
    main()