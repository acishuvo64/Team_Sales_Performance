# Sales Officer Performance Dashboard (Streamlit)

Boss শুধু link-এ ক্লিক করলেই সর্বশেষ ড্যাশবোর্ড দেখবে — **কোনো password
নেই, কোনো upload button নেই।** Data আসে সরাসরি `data/latest_report.xlsx`
থেকে, যেটা তুমি নিজে GitHub repo-তে replace করবে।

## 📁 Files

```
jarvis_dashboard/
├── app.py                 <- Streamlit UI
├── data_processing.py     <- সব হিসাব-নিকাশের লজিক
├── requirements.txt
├── data/
│   └── latest_report.xlsx <- এই ফাইলটাই replace করবে প্রতিদিন
└── README.md
```

## 🚀 লোকালি চালানো

```bash
pip install -r requirements.txt
streamlit run app.py
```

ব্রাউজারে `http://localhost:8501` খুলবে — সরাসরি ড্যাশবোর্ড দেখাবে,
কোনো login বা upload স্ক্রিন নেই।

## ☁️ Streamlit Community Cloud-এ Deploy (Boss-কে যে link দিবে)

1. এই ফোল্ডারটা একটা GitHub repo-তে push করো (private repo রাখাই ভালো,
   কারণ এতে sales data থাকবে)
2. https://share.streamlit.io -এ গিয়ে "New app" → repo সিলেক্ট করো →
   main file: `app.py`
3. Deploy হয়ে গেলে একটা স্থায়ী link পাবে (যেমন
   `https://your-app.streamlit.app`) — এটাই Boss-কে দাও
4. Boss শুধু link খুলবে, সাথে সাথে dashboard দেখবে — কোনো password বা
   upload button নেই

## 🔄 প্রতিদিনের workflow (তুমি করবে)

1. প্রতিদিন সেই দিনের Excel export করো (আগের মতোই — "Outlet Targt + Memo",
   "SO Activity", "Attendance" — এই ৩টা শীট সহ)
2. তোমার লোকাল `jarvis_dashboard/data/` ফোল্ডারে গিয়ে পুরনো ফাইলটা
   মুছে নতুন ফাইলটা **ঠিক এই নামেই** রাখো: `latest_report.xlsx`
3. Terminal-এ:
   ```bash
   git add data/latest_report.xlsx
   git commit -m "update: daily report"
   git push
   ```
4. Streamlit Cloud নিজে থেকেই নতুন push দেখে redeploy করবে (কয়েক সেকেন্ড
   থেকে ১-২ মিনিট লাগতে পারে) — এরপর Boss link খুললেই নতুন data দেখবে।

> চাইলে GitHub-এর ওয়েব ইন্টারফেস থেকেও `data/latest_report.xlsx` ফাইলটা
> সরাসরি আপলোড/রিপ্লেস করা যায় (repo → data ফোল্ডার → "Add file" →
> "Upload files") — terminal ছাড়াই।

## 📊 প্রতিটা রিকোয়ারমেন্ট কোথায় আছে

| তোমার চাহিদা | ড্যাশবোর্ডে কোথায় |
|---|---|
| Daily late count | Tab 2 → "Late Count & Attendance Summary" + day-by-day expander |
| Total late percentage | Tab 2, "Late %" কলাম |
| 1st visit | Tab 2 → "First Visit (Check-in) Time" |
| Market stay/idle time | Tab 3 → "Market Stay / Idle Time" |
| Memo count vs target 8 | Tab 3 → "Memo Performance" |
| Top 10 good performer | Tab 1 → "Top 10 Good Performers" |
| Top 10 bad performer | Tab 1 → "Top 10 Bad Performers" |
| Group-wise / Top / Bad performer chart | Tab 1, সব চার্ট |
| RSM-wise Top/Less performer graph | Tab 1 → নিচের দিকে (RSM data না থাকলে Zone দিয়ে) |
| Day-wise most visited route | Tab 4 → "Most Visited Route per SO" |
| একই মার্কেটে বারবার ভিজিট | Tab 4 → "Repeat Market Visits" |
| Total outlet visit → day-wise average → 20-target % | Tab 3 → "Outlet Visit Performance" |
| 60%-এর নিচে লাল মার্ক | সব % কলামেই automatic লাল হাইলাইট |
| Decimal ছাড়া, সব integer | সব জায়গায় round করা |

## 📑 Excel ফাইলের গঠন (৩টা শীট)

1. **"Outlet Targt + Memo"** — Staff ID, Sr Name, Total Outlet Target,
   Total Outlet Visit, Percentage Of Visit, Total Shop Memo Target,
   Total Shop Memo Count, Memo % — এই শীট থেকেই official Outlet Visit %
   আর Memo % সরাসরি নেওয়া হয় (নিজে হিসাব করা হয় না, কারণ এটাই
   company-র official সংখ্যা)।
2. **"SO Activity"** — প্রতিটা মার্কেট ভিজিটের row। Staff-wise total বের
   করতে `Number Of Outlet Visit` আর `Number Of Ordered Shop` কলাম দুটো
   **sum** করা হয়েছে (row count না)।
3. **"Attendance"** — Attendance Status (Present/Absent) আর Late Status
   (On Time/Late/Absent) থেকে Present %, Late % বের করা হয়।

## ⚠️ গুরুত্বপূর্ণ Assumptions

1. **"Memo"** = `Number Of Ordered Shop` কলাম।
2. **"1st Visit"** = দিনের প্রথম check-in সময় (Attendance শীট থেকে)।
3. **"Market stay/idle time"** এখন হিসাব করা যাচ্ছে না, কারণ শুধু check-in
   সময় আছে, check-out সময় নেই। ভবিষ্যতে export-এ check-out সময় যোগ হলে
   কোড নিজে থেকেই এই সেকশন চালু করে দেবে।
4. **RSM কলাম** থাকলে RSM দিয়ে group হয়, না থাকলে Zone দিয়ে।
5. **Outlet Visit % / Memo %** = "Outlet Targt + Memo" শীটের official
   সংখ্যা। "Avg Outlets/Day" / "Avg Memo/Day" প্রতিটা SO-র নিজের active
   days দিয়ে হিসাব করা — এগুলোই Top/Bad performer লিস্টে ব্যবহৃত হয়
   (≥20/day ভালো, <15/day খারাপ)।
6. **Repeat market visit** = একই আউটলেট (Market Id) আলাদা তারিখে
   একাধিকবার ভিজিট হলে।
