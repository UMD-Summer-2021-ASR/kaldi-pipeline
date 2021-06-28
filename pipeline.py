import datetime
from posixpath import join
from re import sub
import luigi
import os
from pathlib import PurePath,Path
from shelldon import shelldon
import audioread
from datetime import datetime


class QuizzrConfig(luigi.Config):
    store_path = luigi.Parameter(default="{}/quizzr/processed_data".format(Path.home()))
    audio_path = luigi.Parameter(default="{}/quizzr/data".format(Path.home()))

class ProcessData(luigi.Task):
    date_interval = luigi.DateHourParameter(default=datetime.today())
    sample_rate = luigi.IntParameter()
    mfcc_conf = luigi.Parameter()
    subpath= luigi.Parameter()

    def output(self):
        return luigi.LocalTarget(QuizzrConfig().store_path + "/process_log_{}_{}.log".format(self.date_interval.__str__(),self.sample_rate))

    def run(self):
        audio_path = PurePath(QuizzrConfig().audio_path)
        store_path = PurePath(os.path.join(QuizzrConfig().store_path,self.subpath))
        os.makedirs(store_path.joinpath("audio"),exist_ok=True)
        print("a",audio_path)
        wav_scp = open(os.path.join(store_path,"wav.scp"),"w")
        segments = open(os.path.join(store_path,"segments"),"w")
        utt2spk = open(os.path.join(store_path,"utt2spk"),"w")
        for file in os.listdir(audio_path):
            print(file)
            if file.endswith(".wav"):
                shelldon.call("sox {} -r {} -c 1 -b 16 --endian little {}/audio/{}.wav".format(audio_path.joinpath(file),self.sample_rate,store_path , Path(file).stem))
        for file in os.listdir(audio_path):
            if file.endswith(".wav"):
                wav_scp.write("{}  {}\n".format(Path(file).stem , store_path.joinpath("audio",file)))
                utt2spk.write("{0}_001 {0}\n".format(Path(file).stem ))
                segments.write("{0}_001 {0} 0.0 {1}\n".format(Path(file).stem,audioread.audio_open(audio_path.joinpath(file)).duration))
        wav_scp.close()
        segments.close()
        utt2spk.close()
        shelldon.call("utils/fix_data_dir.sh {}".format(store_path))
        shelldon.call("steps/make_mfcc.sh --nj 1 --mfcc-config conf/{0} {1} {1}/make_mfcc {1}/mfcc".format(self.mfcc_conf,store_path))
        shelldon.call("steps/compute_vad_decision.sh {0} {0}/vad".format(store_path))
        shelldon.call("diarization/vad_to_segments.sh {0} {0}/cleaned".format(store_path))
        with self.output().open("w") as outfile:
            outfile.write(store_path.__str__())


class SpeakerDiarization(luigi.Task):

    detect_num_speakers = luigi.BoolParameter(default=False)
    max_num_speakers = luigi.IntParameter(default=2)
    threshold = luigi.FloatParameter(default=0.5)
    date_interval = luigi.DateHourParameter(default=datetime.today())
    

    def requires(self):
        return ProcessData(sample_rate=8000,subpath="diar",mfcc_conf="mfcc.conf")

    def run(self):
        store_path = self.input().open("r").read()
        print(store_path)
        if not os.path.exists(os.path.join(store_path,"reco2num_spk")):
            with open(os.path.join(store_path,"reco2num_spk"),"w") as f:
                for file in os.listdir(os.path.join(store_path,"audio")):
                    f.write("{} {}\n".format(Path(file).stem,self.max_num_speakers))
        cleaned_path = os.path.join(store_path,"cleaned")
        shelldon.call("local/nnet3/xvector/prepare_feats.sh --nj 1 {0} {1}/cmnn {1}/cmnn".format(cleaned_path,store_path))
        shelldon.call("cp {0}/cleaned/segments {0}/cmnn/segments".format(store_path))
        shelldon.call("diarization/nnet3/xvector/extract_xvectors.sh --nj 1 --window 1.5 --period 0.75 --apply-cmn false models/0003_sre16_v2_1a/exp/xvector_nnet_1a {0}/cmnn {0}/xvectors".format(store_path))
        shelldon.call("diarization/nnet3/xvector/score_plda.sh --target-energy 0.9 --nj 1 models/0003_sre16_v2_1a/exp/xvectors_sre_combined/ {0}/xvectors {0}/xvectors/plda_scores".format(store_path))
        if not self.detect_num_speakers:
            shelldon.call("diarization/cluster.sh --nj 1 --reco2num-spk {0}/reco2num_spk {0}/xvectors/plda_scores {0}/xvectors/plda_scores_speakers".format(store_path))
        else:
            shelldon.call("diarization/cluster.sh --nj 1 --threshold {0} {1}/xvectors/plda_scores {1}/xvectors/plda_scores_speakers".format(self.threshold,store_path))

    def output(self):
        return luigi.LocalTarget(os.path.join(QuizzrConfig().store_path,"diar","xvectors","plda_scores_speakers","rttm"))


class AutomaticSpeechRecognition(luigi.Task):

    date_interval = luigi.DateHourParameter(default=datetime.today())
    model_directory = luigi.Parameter(default="models/asr")
    
    def requires(self):
        return ProcessData(sample_rate=16000,subpath="asr",mfcc_conf="asr.conf")
        
    def run(self):
        shelldon.call("scripts/asr.sh {} {}".format(self.model_directory,os.path.join(QuizzrConfig().store_path,"asr","cleaned")))

    def output(self):
        return luigi.LocalTarget(os.path.join(QuizzrConfig().store_path,"asr","cleaned","one-best-hypothesis.txt"))
       

class ForcedAlignment(luigi.Task):

    date_interval = luigi.DateHourParameter(default=datetime.today())
    

    def requires(self):
        return [AutomaticSpeechRecognition(),SpeakerDiarization()]

    def output(self):
        return luigi.LocalTarget(QuizzrConfig().store_path + "/process_log_{}_{}.log".format(self.date_interval.__str__(),"falign"))

    def run(self):
        shelldon.call("python scripts/convert_vtt.py -i {0}/asr/cleaned/final.ctm  -r {0}/diar/xvectors/plda_scores_speakers/rttm -o {0}/vtt".format(QuizzrConfig().store_path))
        with self.output().open("w") as outfile:
                outfile.write("DONE")


class QuizzrPipeline(luigi.WrapperTask):
    def requires(self):
        return [ForcedAlignment()]


if __name__=="__main__":
    luigi.build([QuizzrPipeline()],workers=2, local_scheduler=True)
