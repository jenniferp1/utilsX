import os
import shutil

def mv_file(fname, folder):

  source = fname
  fn = fname.split("/")[-1]
  dest = f"{folder}/{fn}"

  shutil.move(source,dest)

  return
