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

## Task 2

[View Solution](task_2)

გაარჩიეთ მომაგრებული Python-ის სკრიპტი, გაეცანით input("question ?") ფუნქციონალს.
ეს Python-ის სკრიპტი მუშაობდა https://type.fit/api/quotes-დან წამოღებულ, ცნობილი ადამიანების ციტატებზე. თქვენი დავალებაა ეს სკრიპტი გადააწყოთ https://api.quotable.kurokeita.dev/api/quotes/random ენდპოინტზე და შეასრულოთ შემდეგი დავალებები:

- თქვენს CLI სკრიპტს დაუმატეთ `--inspire` flag-ი, რომელიც დააბრუნებს random ციტატას მოცემული API-დან.
- `--inspire "Linus Torvalds"` flag-მა უნდა დააბრუნოს მხოლოდ შესაბამისი ავტორის ციტატა. დაიხმარეთ https://api.quotable.kurokeita.dev/.
- `"bucket_name" --inspire "Linus Torvalds" -save` flag-მა უნდა დააბრუნოს ციტატა და შეინახოს თქვენს მიერ პარამეტრად გადაცემულ bucket-ში .json ფაილად.
