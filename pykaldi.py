import subprocess
import os
from pathlib import Path
from shelldon import shelldon
import audioread

class ForcedAligner:
    def __init__(self) -> None:
        pass

    def align(self,audio:str,transcript:str):
        process = subprocess.Popen("bash falign/align.sh s3/text/{0}.txt s3/audio/{0}.wav data/lang_chain/ s3/faligned/{0}.out.ctm  s3/faligned/{0}.out_phone.ctm  s3/faligned/{0}.out_transid_seq.txt  s3/faligned/{0}.lpf.txt s3/faligned/{0}.vtt".format(id), shell=True, stdout=subprocess.PIPE)
        process_return = process.stdout.read()
        with open("falign.log","w") as f:
            f.write(process_return)

class SpeechRecgnizer:
    def __init__(self) -> None:
        pass

    def transcribe():
        pass

class SpeechDiarization:
    def __init__(self) -> None:
        pass

    def diar(self,store_path,cleaned_path:str) -> None:
        shelldon.call("local/nnet3/xvector/prepare_feats.sh --nj 1 {} {}/cmnn {}/cmnn".format(cleaned_path,store_path,store_path))
        shelldon.call("cp {}/cleaned/segments {}/cmnn/segments".format(store_path,store_path))
        shelldon.call("diarization/nnet3/xvector/extract_xvectors.sh --nj 1 --window 1.5 --period 0.75 --apply-cmn false models/0003_sre16_v2_1a/exp/xvector_nnet_1a {}/cmnn {}/xvectors".format(store_path,store_path))
        shelldon.call("diarization/nnet3/xvector/score_plda.sh --target-energy 0.9 --nj 1 models/0003_sre16_v2_1a/exp/xvectors_sre_combined/ {}/xvectors {}/xvectors/plda_scores".format(store_path,store_path))
        shelldon.call("diarization/cluster.sh --nj 1 --reco2num-spk {0}/cleaned/reco2num_spk {0}/xvectors/plda_scores {0}/xvectors/plda_scores_speakers".format(store_path))

class Preprocessor:
    def __init__(self) -> None:
        pass

    def process_audio(self,path:str,store_path:str) -> None:
        os.makedirs(store_path+"/conv" ,exist_ok=True)
        with open(store_path + "/wav.scp","w") as f:
            for file in os.listdir(path):
                if file.endswith(".wav"):
                    print(path + "/" + file)
                    shelldon.call("sox {} -r 8000 -c 1 {}/conv/{}.wav".format(path + "/" + file,store_path , Path(file).stem))
        with open(store_path + "/wav.scp","w") as f:
            for file in os.listdir(store_path+"/conv"):
                if file.endswith(".wav"):
                    f.write("{}  {}\n".format(Path(file).stem , store_path+"/conv" + "/" + file))
        with open(store_path + "/segments","w") as f:
            for file in os.listdir(path):
                if file.endswith(".wav"):
                    f.write("{}_001 {} 0.0 {}\n".format(Path(file).stem, Path(file).stem, audioread.audio_open(path+"/"+file).duration))
        with open(store_path + "/utt2spk","w") as f:
            for file in os.listdir(path):
                if file.endswith(".wav"):
                    f.write("{}_001 {}\n".format(Path(file).stem , Path(file).stem ))
        shelldon.call("utils/fix_data_dir.sh {}".format(store_path))
        shelldon.call("steps/make_mfcc.sh --nj 1 --mfcc-config conf/mfcc.conf {} log/make_mfcc {}/mfcc".format(store_path,store_path))
        shelldon.call("steps/compute_vad_decision.sh {} {}/vad".format(store_path,store_path))
        shelldon.call("diarization/vad_to_segments.sh {} {}/cleaned".format(store_path,store_path))
        with open(store_path + "/cleaned/reco2num_spk","w") as f:
            for file in os.listdir(path):
                if file.endswith(".wav"):
                    f.write("{} 2\n".format(Path(file).stem ))
                
            
if __name__ == "__main__":
    # Preprocessor().process_audio("/home/mshivam/quizzr/data","processed_data")
    SpeechDiarization().diar("processed_data","processed_data/cleaned")