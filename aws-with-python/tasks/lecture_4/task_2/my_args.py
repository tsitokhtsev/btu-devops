from os import getenv


def bucket_arguments(parser):
    parser.add_argument(
        "name",
        type=str,
        help="Pass bucket name.",
    )

    parser.add_argument(
        "-cb",
        "--create_bucket",
        help="Flag to create bucket.",
        choices=["False", "True"],
        type=str,
        nargs="?",
        # https://jdhao.github.io/2018/10/11/python_argparse_set_boolean_params
        const="True",
        default="False",
    )

    parser.add_argument(
        "-bc",
        "--bucket_check",
        help="Check if bucket already exists.",
        choices=["False", "True"],
        type=str,
        nargs="?",
        const="True",
        default="True",
    )

    parser.add_argument(
        "-region",
        "--region",
        nargs="?",
        type=str,
        help="Region variable.",
        default=getenv("aws_s3_region_name", "us-west-2"),
    )

    parser.add_argument(
        "-db",
        "--delete_bucket",
        help="flag to delete bucket",
        choices=["False", "True"],
        type=str,
        nargs="?",
        const="True",
        default="False",
    )

    parser.add_argument(
        "-be",
        "--bucket_exists",
        help="flag to check if bucket exists",
        choices=["False", "True"],
        type=str,
        nargs="?",
        const="True",
        default="False",
    )

    parser.add_argument(
        "-rp",
        "--read_policy",
        help="flag to read bucket policy.",
        choices=["False", "True"],
        type=str,
        nargs="?",
        const="True",
        default="False",
    )

    parser.add_argument(
        "-arp",
        "--assign_read_policy",
        help="flag to assign read bucket policy.",
        choices=["False", "True"],
        type=str,
        nargs="?",
        const="True",
        default="False",
    )

    parser.add_argument(
        "-amp",
        "--assign_missing_policy",
        help="flag to assign read bucket policy.",
        choices=["False", "True"],
        type=str,
        nargs="?",
        const="True",
        default="False",
    )

    parser.add_argument(
        "-lo",
        "--list_objects",
        type=str,
        help="list bucket object",
        nargs="?",
        const="True",
        default="False",
    )

    parser.add_argument(
        "-ben",
        "--bucket_encryption",
        type=str,
        help="bucket object encryption",
        nargs="?",
        const="True",
        default="False",
    )

    parser.add_argument(
        "-rben",
        "--read_bucket_encryption",
        type=str,
        help="list bucket object",
        nargs="?",
        const="True",
        default="False",
    )

    parser.add_argument(
        "-vers",
        "--versioning",
        type=str,
        help="list bucket object",
        nargs="?",
        default=None,
    )

    parser.add_argument(
        "-o_b",
        "--organize_bucket",
        help="list versions",
        action="store_true",
    )

    return parser


def object_arguments(parser):
    parser.add_argument(
        "name",
        nargs="?",
        type=str,
        help="Pass object name.",
    )

    parser.add_argument(
        "bucket_name",
        type=str,
        help="Pass bucket name.",
    )

    parser.add_argument(
        "-du",
        "--download_upload",
        choices=["False", "True"],
        help="download and upload to bucket",
        type=str,
        nargs="?",
        const="True",
        default="False",
    )

    parser.add_argument(
        "-ol",
        "--object_link",
        type=str,
        help="link to download and upload to bucket",
        default=None,
    )

    parser.add_argument(
        "-loc_o",
        "--local_object",
        type=str,
        help="upload local object",
        default=None,
    )

    parser.add_argument(
        "-k_f_n",
        "--keep_file_name",
        help="file name",
        action="store_false",
    )

    parser.add_argument(
        "-u_t",
        "--upload_type",
        type=str,
        help="upload function type",
        choices=["upload_file", "upload_fileobj", "put_object", "multipart_upload"],
    )

    parser.add_argument(
        "-l_v",
        "--list_versions",
        help="list versions",
        action="store_true",
    )

    parser.add_argument(
        "-r_b_t",
        "--roll_back_to",
        type=str,
        help="rollback to",
        default=None,
    )

    parser.add_argument(
        "-cov",
        "--cleanup_old_versions",
        nargs="+",
        metavar="FILE_NAME",
        type=str,
        help="List of file names to clean up old versions (older than 6 months).",
        default=None,
    )

    return parser
