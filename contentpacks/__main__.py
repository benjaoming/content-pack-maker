"""
makepack

Usage:
  makecontentpacks ka-lite <lang> <version> [--subtitlelang=subtitle-lang --contentlang=content-lang --interfacelang=interface-lang --videolang=video-lang --out=outdir --logging=log_file --no-assessment-items --no-subtitles]
  makecontentpacks -h | --help
  makecontentpacks --version

"""
from docopt import docopt
from pathlib import Path
from contentpacks.khanacademy import retrieve_language_resources, apply_dubbed_video_map, retrieve_html_exercises, \
    retrieve_all_assessment_item_data
from contentpacks.utils import translate_nodes, \
    remove_untranslated_exercises, bundle_language_pack, separate_exercise_types, \
    generate_kalite_language_pack_metadata, translate_assessment_item_text

import logging

def make_language_pack(lang, version, sublangargs, filename, no_assessment_items, no_subtitles):
    node_data, subtitle_data, interface_catalog, content_catalog, dubmap = retrieve_language_resources(version, sublangargs, no_subtitles)

    subtitles, subtitle_paths = subtitle_data.keys(), subtitle_data.values()

    node_data = translate_nodes(node_data, content_catalog)
    node_data = list(node_data)
    node_data, dubbed_video_count = apply_dubbed_video_map(node_data, dubmap, subtitles, sublangargs["video_lang"])

    html_exercise_ids, assessment_exercise_ids, node_data = separate_exercise_types(node_data)
    html_exercise_path, translated_html_exercise_ids = retrieve_html_exercises(html_exercise_ids, lang)

    # now include only the assessment item resources that we need
    all_assessment_data, all_assessment_files = retrieve_all_assessment_item_data() if not no_assessment_items else ([], set())

    assessment_data = translate_assessment_item_text(all_assessment_data, content_catalog) if lang != "en" else all_assessment_data

    node_data = remove_untranslated_exercises(node_data, translated_html_exercise_ids, assessment_data) if lang != "en" else node_data

    pack_metadata = generate_kalite_language_pack_metadata(lang, version, interface_catalog, content_catalog, subtitles,
                                                           dubbed_video_count)

    if no_assessment_items:
        # Only bundle assessment item asset files for the English language pack
        all_assessment_files = []

    bundle_language_pack(str(filename), node_data, interface_catalog, interface_catalog,
                         pack_metadata, assessment_data, all_assessment_files, subtitle_paths)


def normalize_sublang_args(args):
    """
    Transform the command line arguments we have into something that conforms to the retrieve_language_resources interface.
    This mostly means using the given lang parameter as the default lang, overridable by the different sublang args.
    """
    return {
        "video_lang": args['--videolang'] or args['<lang>'],
        "content_lang": args['--contentlang'] or args['<lang>'],
        "interface_lang": args['--interfacelang'] or args['<lang>'],
        "subtitle_lang": args['--subtitlelang'] or args['<lang>'],
    }


def main():
    args = docopt(__doc__)

    assert args["ka-lite"], ("Sorry, content packs for non-KA Lite "
                             "software aren't implemented yet.")
    del args["ka-lite"]

    lang = args["<lang>"]
    version = args["<version>"]
    out = Path(args["--out"]) if args['--out'] else Path.cwd() / "{lang}.zip".format(lang=lang)

    sublangs = normalize_sublang_args(args)

    no_assessment_items = args["--no-assessment-items"]
    no_subtitles = args['--no-subtitles']

    log_file = args["--logging"] or "debug.log"

    logging.basicConfig(level=logging.INFO)

    try:
        make_language_pack(lang, version, sublangs, out, no_assessment_items, no_subtitles)
    except Exception:           # This is allowed, since we want to potentially debug all errors
        import os
        if not os.environ.get("DEBUG"):
            raise
        else:
            import pdb
            pdb.post_mortem()


if __name__ == "__main__":
    main()
