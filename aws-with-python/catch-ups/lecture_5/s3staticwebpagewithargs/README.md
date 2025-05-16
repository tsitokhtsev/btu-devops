# AWS BTU

# S3 CLI + host static

That's S3 CLI tool, created for educational purposes. Don't forget to check `.env.example` file to see all the required credentials to allow CLI script work correctly.

## Install

First install:

```
https://github.com/ahupp/python-magic
```

```
poetry install
```

## Usage

First run in shell help command, to see the message about avaliable CLI functions, it can listen for passed `-h`, or `--help`:

```shell
python main.py -h
```

## Bucket

Commands works without `""` too.

### Create bucket

```shell
python main.py bucket "any-name-for-s3" -cb
```

### Create bucket and Enable Versining

```shell
python main.py bucket "bucket-with-vers-2" -cb -vers True
```

### Organize bucket per extensions

```shell
python main.py bucket "bucket-with-vers" -o_b
```

````

### Show bucket's objects tree

```shell
python main.py bucket "bucket-with-vers" --show_bucket_tree
````

## Object

Upload local object from /static folder.

```shell
python main.py object "bucket-with-vers" --local_object "important.txt" --upload_type "upload_file"
```

Upload object link.

```shell
python main.py object bucket_name "new-bucket-btu-7" -ol "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4" -du
```

List object versions

```shell
python main.py object "important.txt" "bucket-with-vers" -l_v
```

Rollback to version

```shell
python main.py object "important.txt" "bucket-with-vers" -r_b_t "En8tj6pxH3nduvOzGpEs5RP5QN6M5UQ6"
```

## List Buckets

```shell
python main.py list_buckets
```

## Host

Enable public read permission on Bucket

```shell
python main.py bucket "your-bucket-name" --assign_read_policy
```

Set "WebsiteConfiguration"

```shell
python main.py host "your-bucket-name" --website_configuration True
```

Host static file

```shell
python main.py host "your-bucket-name" --host_static "index.html"
```

Host static file with folders

```shell
python main.py host "your-bucket-name" --host_static "separate_project"
```
