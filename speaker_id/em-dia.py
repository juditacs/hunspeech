import subprocess
from argparse import ArgumentParser
from os.path import basename, splitext
import logging


class EmDiarizer:

    def __init__(self, shout_dir, shout_model):

        self.src_dir = shout_dir
        self.model = shout_model

    def derive_fns(self, input_fn, sad_fn, output_dir):

        self.steps = []
        base_fn = basename(input_fn)
        base, extension = splitext(base_fn)
        self.input_fn = input_fn
        if extension == '.raw':
            self.raw_fn = input_fn
        else:
            self.steps.append(self.convert_to_raw)
            self.raw_fn = '{}/{}.raw'.format(output_dir, base)
        if sad_fn:
            self.sad_fn = sad_fn
        else:
            self.steps.append(self.run_sad)
            self.sad_fn = '{}/{}.sad'.format(output_dir, base)
        self.steps.append(self.run_clustering)
        self.log_fn = '{}/{}.log'.format(output_dir, base)
        self.dia_fn = '{}/{}.dia'.format(output_dir, base)

    def convert_to_raw(self):
        subprocess.check_call(['sox', self.input_fn, '-c', '1', '-r', '16000',
            '--bits', '16', '--endian', 'little', self.raw_fn],
            stdout=self.log, stderr=self.log)

    def run_sad(self):
        src = '{}/release-2010-version-0-3/release/src/shout_segment'\
                .format(self.src_dir)
        subprocess.check_call([src, '-a', self.raw_fn, '--am-segment',
            self.model, '-mo', self.sad_fn], stdout=self.log, stderr=self.log)

    def run_clustering(self):
        src = '{}/release-2010-version-0-3/release/src/shout_cluster'\
                .format(self.src_dir)
        subprocess.check_call([src, '-a', self.raw_fn, '-mo', self.dia_fn,
            '-mi', self.sad_fn], stdout=self.log, stderr=self.log)

    def process(self, input_fn, sad_out, output_dir):

        self.derive_fns(input_fn, sad_out, output_dir)
        self.log = open(self.log_fn, 'a')
        for step in self.steps:
            try:
                logging.info('{} ...'.format(step.__name__))
                self.log.write('{}:\n'.format(step.__name__))
                self.log.flush()
                step()
                self.log.flush()
            except subprocess.CalledProcessError:
                logging.info(
                        'An error occured, see {}; exiting'.format(
                            self.log_fn))
                quit()
        self.log.close()


def get_args():

    p = ArgumentParser()
    p.add_argument('input_fn')
    p.add_argument('output_dir')
    p.add_argument('shout_dir')
    p.add_argument('-m', '--shout_model')
    p.add_argument('-s', '--sad_fn')
    args = p.parse_args()
    return args


def main():

    logging.basicConfig(level=logging.INFO,
            format='%(asctime)s : %(module)s (%(lineno)s) ' +\
                    '- %(levelname)s - %(message)s')
    args = get_args()
    output_dir = args.output_dir
    shout_dir = args.shout_dir
    shout_model = args.shout_model
    sad_fn = args.sad_fn
    input_fn = args.input_fn
    if shout_model is None and sad_fn is None:
        logging.info('Either shout model file or SAD model' +\
                'file is needed, exiting')
        quit()
    a = EmDiarizer(shout_dir, shout_model)
    a.process(input_fn, sad_fn, output_dir)

if __name__ == '__main__':
    main()
