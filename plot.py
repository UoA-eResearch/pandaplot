#!/usr/bin/env python

import argparse
import pandas as pd
import math
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import os

parser = argparse.ArgumentParser(description='Make a graph')
parser.add_argument('-c', '--colormap', default="jet", help='Which colorscheme to use')
parser.add_argument('-f', '--file', default="Plot_Data_Elem", help='The file to read in')
parser.add_argument('-a', '--axes', default='r,z,P', help='Which columns to plot, in the x y and z dimensions. Comma separated, defaults to r,z,P')
parser.add_argument('-al', '--axeslabels', help='Labels for the x,y,z axes')
parser.add_argument('-s', '--save', action='store_true', help='Whether to save the figure or display it')
parser.add_argument('-o', '--output_filename', help='The filename to save the resulting figure to')
parser.add_argument('-r', '--recursive', action='store_true', help='Whether to traverse the directory tree looking for FILE')
parser.add_argument('-od', '--output_directory', default="plots", help='When running recursively, which directory to save plots to')
parser.add_argument('-e', '--extent', help='Limit the drawn area. Left, right, bottom, top.')
parser.add_argument('-t', '--ticks', help='Number of ticks', default=5)
parser.add_argument('-fs', '--font_size', help='Font size', type=int, default=10)
parser.add_argument('-z', '--zones', help='Which zones to plot')
parser.add_argument('-zf', '--zone_factor', default=365, type=int, help='Factor to multiply the zone number by')
parser.add_argument('-sd', '--sample_data', action='store_true', help='Plot some sample data')

args = parser.parse_args()
axes = args.axes.split(",")
axeslabels = []
if args.axeslabels:
  axeslabels = args.axeslabels.split(",")
else:
  axeslabels = axes
extent = None
if args.extent:
  extent = [int(i) for i in args.extent.split(",")]
zones = None
if args.zones:
  zones = [int(i) for i in args.zones.split(",")]
figtitle = "{} vs {} vs {}".format(*axes)

def search_files(directory='.'):
  hits = []
  for dirpath, dirnames, files in os.walk(directory):
    if args.file in files:
      hits.append(os.path.join(dirpath, args.file))
  return hits

def read_file(filename):
  global zones
  with open(filename) as f:
    lines = f.readlines()

  headers = lines[0].strip().replace("Variables =", "").split()
  headers.append("zone")
  zone = 0
  data = []
  for line in lines[2:]:
    if "ZONE" in line:
      zone += 1
    elif line.strip() != "":
      parsed_line = [float(x) for x in line.split()]
      parsed_line.append(zone)
      data.append(parsed_line)
  df = pd.DataFrame(data, columns = headers)
  if zones:
    if zone < max(zones):
      print("ERROR: {} does not exist in {} - {} is the highest zone".format(max(zones), filename, zone))
      exit(1)
  else:
    zones = list(range(zone + 1))
  return df

def plot(df):
  fig, subplots = plt.subplots(nrows=len(zones), sharex=True, figsize=(10,10), squeeze=False)
  subplots = subplots.ravel()

  if extent:
    x = df[axes[0]]
    y = df[axes[1]]
    mask = (x >= extent[0]) & (x <= extent[1]) & (y >= extent[2]) & (y <= extent[3])
    masked_df = df[mask]
    zmin = masked_df[axes[2]].min()
    zmax = masked_df[axes[2]].max()
  else:
    zmin = df[axes[2]].min()
    zmax = df[axes[2]].max()

  for i, z in enumerate(zones):
    dz = df[df["zone"] == z]
    ax = subplots[i]
    piv = pd.pivot_table(dz, values=axes[2], index = axes[1], columns=axes[0])
    im = ax.pcolormesh(piv.columns, piv.index, piv, cmap=args.colormap, vmin=zmin, vmax=zmax)
    ax.yaxis.set_major_locator(ticker.LinearLocator(args.ticks))
    ax.xaxis.set_major_locator(ticker.LinearLocator(args.ticks))
    if extent:
      ax.set_xlim(extent[:2])
      ax.set_ylim(extent[2:])
    ax.set_xlabel(axeslabels[0], fontsize=args.font_size)
    ax.set_ylabel(axeslabels[1], fontsize=args.font_size)
    title = ax.set_title("Day {}".format(z * args.zone_factor), position=(1.01, .5), rotation=-90, horizontalalignment='left', verticalalignment='center', transform=ax.transAxes, fontsize=args.font_size)
    rect = plt.Rectangle(
      (1,1), width=1, height=.05, angle=-90, linewidth=1, transform=ax.transAxes, fill=False, clip_on=False
    )
    ax.add_patch(rect)
    ax.label_outer()

  cb = fig.colorbar(im, ax=subplots, ticks=ticker.LinearLocator(args.ticks), format='%.2e')
  cb.ax.set_title(axeslabels[2], fontsize=args.font_size)
  return fig

if args.recursive:
  files = search_files()
  if not os.path.isdir(args.output_directory):
    os.mkdir(args.output_directory)
  for f in files:
    print("plotting " + f)
    df = read_file(args.file)
    fig = plot(df)
    safe_f = f.replace(args.file, "").replace("/", "_").replace(".", "")
    filename = os.path.join(args.output_directory, safe_f)
    fig.savefig(filename)
elif args.sample_data:
  data = []
  axes = ["x", "y", "z"]
  axeslabels = axes
  zones = [0, 1, 2, 3]
  for zone in zones:
    for x in range(0, 100):
      for y in range(0, 100):
        z = math.sin(x / 50.0) * math.sin(y / 50.0) * zone
        data.append([x, y, z, zone])
  df = pd.DataFrame(data, columns = ["x", "y", "z", "zone"])
  fig = plot(df)
  if args.save:
    fig.savefig("sample.png")
  else:
    plt.show()
else:
  df = read_file(args.file)
  fig = plot(df)
  if args.save:
    if args.output_filename:
      filename = args.output_filename
    else:
      filename = figtitle + ".eps"
    fig.savefig(filename)
  else:
    plt.show()

