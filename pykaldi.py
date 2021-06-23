import subprocess
import json

class ForcedAligner:
    def __init__(self) -> None:
        pass

    def align(self,audio:str,transcript:str):
        process = subprocess.Popen("bash falign/align.sh s3/text/{0}.txt s3/audio/{0}.wav data/lang_chain/ s3/faligned/{0}.out.ctm  s3/faligned/{0}.out_phone.ctm  s3/faligned/{0}.out_transid_seq.txt  s3/faligned/{0}.lpf.txt s3/faligned/{0}.vtt".format(id), shell=True, stdout=subprocess.PIPE)
        process_return = process.stdout.read()
        with open("falign.log","w") as f:
            f.write(process_return)
