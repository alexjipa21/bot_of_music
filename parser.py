
import argparse
import os
parser = argparse.ArgumentParser()
parser.add_argument('--name', type=str, required=True)
parser.add_argument('--token', default=os.environ.get('-t'))
args = parser.parse_args()#
print('Hello,', args.name)
