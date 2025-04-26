# Lecture 5

## Task 1

[View Solution](task_1)

მოძებნეთ ნებისმიერი web გვერდის source, მაგალითად https://github.com/do-community/html_demo_site. რის შემდეგაც დაწერეთ CLI script-ი, რომელიც:

- ატვირთავს source-ს თქვენს მიერ არგუმენტად მიწოდებულ bucket-ში.
- გაუწერს ამ bucket-ს "WebsiteConfiguration".
- მისცემს შესაბამის permission-ს.
- დაგიბრუნებთ თქვენი სტატიკური web გვერდის მისამართს.

გაითვალისწინეთ, ეს მოქმედებები უნდა შესრულდეს მხოლოდ 1 ბრძანების გამოძახებით, მაგალითად:

```shell
python main.py host "my-s3-static-host" --source "project_folder"
```
