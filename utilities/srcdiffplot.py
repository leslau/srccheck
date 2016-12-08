"""Source Code Diff Plot

Usage:
  srcdiffplot   --before=<inputUDB> --after=<inputUDB> \r\n \
                [--dllDir=<dllDir>]\r\n \
                [--skipLibs=<skipLibs>]\r\n \
                [--fileQuery=<fileQuery>]\r\n \
                [--classQuery=<classQuery>]\r\n \
                [--routineQuery=<routineQuery>]\r\n \
                [--fileMetrics=<fileMetrics>]\r\n \
                [--classMetrics=<classMetrics>]\r\n \
                [--routineMetrics=<routineMetrics>]\r\n \
                [--regexTraverseFiles=<regexTraverseFiles>] \r\n \
                [--regexIgnoreFiles=<regexIgnoreFiles>] \r\n \
                [--regexIgnoreClasses=<regexIgnoreClasses>] \r\n \
                [--regexIgnoreRoutines=<regexIgnoreRoutines>] \r\n \
                [--verbose]

Options:
  --before=<inputUDB>                           File path to a UDB with the "before" state of your sources
  --after=<inputUDB>                            File path to a UDB with the "after" state of your sources
  --dllDir=<dllDir>                             Path to the dir with the DLL to the Understand Python SDK.[default: C:/Program Files/SciTools/bin/pc-win64/python]
  --skipLibs=<skipLibs>                         false for full analysis. true if you want to skip libraries you import. [default: true]
  --fileQuery=<fileQuery>                       Kinds of files you want to traverse[default: file ~Unknown ~Unresolved]
  --classQuery=<classQuery>                     Kinds of classes your language has. [default: class ~Unknown ~Unresolved, interface ~Unknown ~Unresolved]
  --routineQuery=<routineQuery>                 Kinds of routines your language has. [default: function ~Unknown ~Unresolved,method ~Unknown ~Unresolved,procedure ~Unknown ~Unresolved,routine ~Unknown ~Unresolved,classmethod ~Unknown ~Unresolved]
  --fileMetrics=<maxFileMetrics>                A CSV containing file metric names you want to plot [default: CountLineCode,CountDeclFunction,CountDeclClass]
  --classMetrics=<classMetrics>                 A CSV containing class metric names you want to plot [default: CountDeclMethod,PercentLackOfCohesion,MaxInheritanceTree,CountClassCoupled]
  --routineMetrics=<maxClassMetrics>            A CSV containing routine metric names you want to plot [default: CountLineCode,CountParams,CyclomaticStrict]
  --regexTraverseFiles=<regexTraverseFiles>     A regex to filter files in / traverse. Defaults to all [default: .*]
  --regexIgnoreFiles=<regexIgnoreFiles>         A regex to filter files out
  --regexIgnoreClasses=<regexIgnoreClasses>     A regex to filter classes out
  --regexIgnoreRoutines=<regexIgnoreRoutines>   A regex to filter routines out
  -v, --verbose                                 If you want lots of messages printed. [default: false]

Errors:
  DBAlreadyOpen        - only one database may be open at once
  DBCorrupt            - bad database file
  DBOldVersion         - database needs to be rebuilt
  DBUnknownVersion     - database needs to be rebuilt
  DBUnableOpen         - database is unreadable or does not exist
  NoApiLicense         - Understand license required

Author:
  Marcio Marchini (marcio@BetterDeveloper.net)

"""

import datetime
import sys
import os
from docopt import docopt
from utilities.utils import stream_of_entity_with_metrics, save_histogram
from utilities import VERSION

def plot_diff_file_metrics (db_before, db_after, cmdline_arguments):
    plot_diff_generic_metrics(db_before, db_after, cmdline_arguments, cmdline_arguments["--fileMetrics"], cmdline_arguments["--fileQuery"], cmdline_arguments.get("--regexIgnoreFiles", None), "File")

def plot_diff_class_metrics (db_before, db_after, cmdline_arguments):
    plot_diff_generic_metrics(db_before, db_after, cmdline_arguments, cmdline_arguments["--classMetrics"], cmdline_arguments["--classQuery"], cmdline_arguments.get("--regexIgnoreClasses", None), "Class")

def plot_diff_routine_metrics (db_before, db_after, cmdline_arguments):
    plot_diff_generic_metrics(db_before, db_after, cmdline_arguments, cmdline_arguments["--routineMetrics"], cmdline_arguments["--routineQuery"], cmdline_arguments.get("--regexIgnoreRoutines", None), "Routine")


def prune_unchanged (before_after, diff_tag):
    return {name:metrics_by_before_after_tag for name, metrics_by_before_after_tag in before_after.items() if diff_tag in metrics_by_before_after_tag}

def _compute_dict_diff (dict_a, dict_b):
    result = {}
    for key_a, value_a in dict_a.items():
        value_b = dict_b.get(key_a, 0)
        result[key_a] = value_b - value_a
    for key_b, value_b in dict_b.items():
        if key_b not in dict_a: # new metric, was not present in the file
            result[key_b] = value_b
    return result

def populate_diffs(before_after_by_ent_name, tag_before, tag_after, tag_diff):
    for file_path, dict_before_after in before_after_by_ent_name.items():
        metrics_before = dict_before_after.get(tag_before, None)
        if metrics_before is None: # new entity, no "before" state
            continue
        metrics_after = dict_before_after.get(tag_after, None)
        if metrics_after is None: # deleted entity, no "after" state
            continue
        if metrics_before == metrics_after: # no diff at all
            continue
        dict_before_after[tag_diff] = _compute_dict_diff(metrics_before, metrics_after)

def plot_diff_generic_metrics (db_before, db_after, cmdline_arguments, metrics_as_string, entityQuery, regex_str_ignore_item, scope_name):
    regex_str_traverse_files = cmdline_arguments.get("--regexTraverseFiles", "*")
    regex_ignore_files = cmdline_arguments.get("--regexIgnoreFiles", None)
    skipLibraries = cmdline_arguments["--skipLibs"] == "true"
    verbose = cmdline_arguments["--verbose"]
    metrics = [metric.strip() for metric in metrics_as_string.split(",")]
    before_after_by_entity_longname = {}
    for entity, container_file, metric_dict in \
            stream_of_entity_with_metrics(db_before.ents(entityQuery), metrics,
                                          verbose, skipLibraries,
                                         regex_str_ignore_item,
                                         regex_str_traverse_files,
                                         regex_ignore_files):
        attribs = {}
        attribs["before"] = metric_dict
        before_after_by_entity_longname[entity.longname()] = attribs
    for entity, container_file, metric_dict in \
            stream_of_entity_with_metrics(db_after.ents(entityQuery), metrics,
                                          verbose, skipLibraries,
                                         regex_str_ignore_item,
                                         regex_str_traverse_files,
                                         regex_ignore_files):
        attribs = before_after_by_entity_longname.get(entity.longname(),{}) # maybe it is already there... maybe not
        attribs["after"] = metric_dict
        before_after_by_entity_longname[entity.longname()] = attribs
    populate_diffs(before_after_by_entity_longname, "before", "after", "diff")
    just_diff = prune_unchanged(before_after_by_entity_longname,"diff")
    print("Diff for scope %s : %s" % (scope_name, just_diff))

def main():
    start_time = datetime.datetime.now()
    arguments = docopt(__doc__, version=VERSION)
    sys.path.append(arguments["--dllDir"]) # add the dir with the DLL to interop with understand
    print ("\r\n====== srcdiffplot by Marcio Marchini: marcio@BetterDeveloper.net ==========")
    print(arguments)
    try:
        import understand
    except:
        print ("Can' find the Understand DLL. Use --dllDir=...")
        print ("Please set PYTHONPATH to point an Understand's C:/Program Files/SciTools/bin/pc-win64/python or equivalent")
        sys.exit(-1)
    try:
        db_before = understand.open(arguments["--before"])
    except understand.UnderstandError as exc:
        print ("Error opening input file: %s" % exc)
        sys.exit(-2)
    try:
        db_after = understand.open(arguments["--after"])
    except understand.UnderstandError as exc:
        print ("Error opening input file: %s" % exc)
        sys.exit(-2)

    print("Processing %s and %s" % (db_before.name(), db_after.name()))
    plot_diff_file_metrics(db_before, db_after, arguments)
    plot_diff_class_metrics(db_before, db_after, arguments)
    plot_diff_routine_metrics(db_before, db_after, arguments)
    end_time = datetime.datetime.now()
    print("\r\n--------------------------------------------------")
    print("Started : %s" % str(start_time))
    print("Finished: %s" % str(end_time))
    print("Total: %s" % str(end_time - start_time))
    print("--------------------------------------------------")
    db_before.close()
    db_after.close()

if __name__ == '__main__':
    main()