# Lecture 6

## Task 1

[View Solution](task_1)

გადააკეთეთ ლექციის დროს გამოყენებული lambda ფუნქცია, დარეგისტრირდით Hugging Face-ზე და მიუთითეთ თქვენი API token-ი.

თქვენმა Lambda ფუნქციამ უნდა შეძლოს, S3 bucket-ში ატვირთული სურათის რამდენიმე Hugging Face მოდელით დამუშავება და დაბრუნებული data-ს შენახვა ცალ-ცალკე json ფაილში.

მაგალითად, დაამუშავეთ თქვენი სურათი:

- https://huggingface.co/google/mobilenet_v1_0.75_192
- https://huggingface.co/microsoft/resnet-50
- https://huggingface.co/nvidia/mit-b0
- https://huggingface.co/hustvl/yolos-tiny

და შეინახეთ შესაბამის json ფაილში სახელით `json/{model_name}_{image_name}.json` (მაგ: `json/mobilenet_{image_name}.json`).
