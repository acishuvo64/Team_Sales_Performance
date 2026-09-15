# Sales Officer Performance Dashboard (Streamlit)

তুমি (Admin) প্রতিদিন একটা Excel আপলোড করবে, Boss শুধু link-এ ক্লিক করলেই
সর্বশেষ ড্যাশবোর্ড দেখতে পাবে — কোনো upload করতে হবে না।

## 📁 Files

```
jarvis_dashboard/
├── app.py                 <- Streamlit UI (তুমি এটাই চালাবে)
├── data_processing.py     <- সব হিসাব-নিকাশের লজিক
├── requirements.txt
├── data/                  <- এখানে সর্বশেষ uploaded Excel সেভ থাকে
└── README.md
```

## 🚀 লোকালি চালানো

```bash
pip install -r requirements.txt
streamlit run app.py
```

ব্রাউজারে `http://localhost:8501` খুলবে। Sidebar-এর **⚙️ Admin** প্যানেলে
password দিয়ে Excel আপলোড করো — এরপর সবাই (এই একই link-এ যারা ঢুকবে) সেই
ডেটাই দেখবে।

## 🔑 Admin Password বদলানো

ডিফল্ট password: `changeme123` — **অবশ্যই বদলে নাও।**

Terminal-এ চালানোর আগে:
```bash
set DASHBOARD_UPLOAD_PASSWORD=তোমার-গোপন-পাসওয়ার্ড      (Windows PowerShell: $env:DASHBOARD_UPLOAD_PASSWORD="...")
streamlit run app.py
```

Streamlit Community Cloud-এ deploy করলে **Settings → Secrets**-এ যোগ করো:
```
DASHBOARD_UPLOAD_PASSWORD = "তোমার-গোপন-পাসওয়ার্ড"
```

## ☁️ Streamlit Community Cloud-এ Deploy (Boss-কে যে link দিবে)

1. এই ফোল্ডারটা একটা GitHub repo-তে push করো (private repo রাখাই ভালো,
   কারণ এতে sales data থাকবে)
2. https://share.streamlit.io -এ গিয়ে "New app" → repo সিলেক্ট করো →
   main file: `app.py`
3. Deploy হয়ে গেলে একটা স্থায়ী link পাবে (যেমন
   `https://your-app.streamlit.app`) — এটাই Boss-কে দাও
4. প্রতিদিন তুমি সেই link-এ গিয়ে Admin প্যানেল থেকে নতুন Excel আপলোড করবে;
   Boss শুধু link খুলবে, upload করার দরকার নেই

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

এই ভার্সনটা তোমার শেষ (সঠিক) ফাইলের গঠন অনুযায়ী বানানো — মোট ৩টা শীট লাগবে:

1. **"Outlet Targt + Memo"** — Staff ID, Sr Name, Total Outlet Target,
   Total Outlet Visit, Percentage Of Visit, Total Shop Memo Target,
   Total Shop Memo Count, Memo % — এই শীট থেকেই official Outlet Visit %
   আর Memo % সরাসরি নেওয়া হয় (নিজে হিসাব করা হয় না, কারণ এটাই
   company-র official সংখ্যা)।
2. **"SO Activity"** — প্রতিটা মার্কেট ভিজিটের row। Staff-wise total বের
   করতে `Number Of Outlet Visit` আর `Number Of Ordered Shop` কলাম দুটো
   **sum** করা হয়েছে (row count না) — এটা "Outlet Targt + Memo" শীটের
   সংখ্যার সাথে মিলিয়ে verify করা হয়েছে।
3. **"Attendance"** — Attendance Status (Present/Absent) আর Late Status
   (On Time/Late/Absent) থেকে Present %, Late % বের করা হয়।

## ⚠️ গুরুত্বপূর্ণ Assumptions (একবার পড়ে নিও)

1. **"Memo"** = `Number Of Ordered Shop` কলাম ধরা হয়েছে (যে দোকানে অর্ডার
   হয়েছে, সেটাই মেমো)।

2. **"1st Visit"** = দিনের প্রথম check-in সময় (Attendance শীট থেকে), কারণ
   Activity শীটে প্রতিটা আউটলেট ভিজিটের আলাদা সময় (timestamp) নেই, শুধু
   তারিখ আছে।

3. **"Market stay/idle time" এখন হিসাব করা যাচ্ছে না** — এই ফাইলের
   Attendance শীটে শুধু check-in সময় (`In Time Only`) আছে, check-out
   সময় (Out Time) বা মোট ঘণ্টার কোনো কলাম নেই। তাই ড্যাশবোর্ডে এই
   সেকশনে একটা তথ্যমূলক নোট দেখাবে। ভবিষ্যতে export-এ check-out সময়
   যোগ হলে কোড নিজে থেকেই এই সেকশন চালু করে দেবে (কিছু বদলাতে হবে না)।

4. **RSM কলাম এবার পূরণ আছে** — তাই "RSM-wise Top/Least Performer" চার্ট
   এখন সরাসরি **RSM** দিয়ে group হচ্ছে (আগে Zone দিয়ে হতো, কারণ তখন RSM
   খালি ছিল)।

5. **Outlet Visit % / Memo %** = "Outlet Targt + Memo" শীটের official
   সংখ্যা (Total Outlet Visit ÷ Total Outlet Target, ইত্যাদি) — পুরো
   রিপোর্ট পিরিয়ডের জন্য fixed target (যেমন ২০/দিন হিসেবে হলে ও পুরো
   পিরিয়ডের target সবার জন্য একই, active days অনুযায়ী কমে না)।
   পাশাপাশি "Avg Outlets/Day" আর "Avg Memo/Day" কলাম দুটো প্রতিটা SO-র
   নিজের active days দিয়ে হিসাব করা — এগুলোই Top/Bad performer লিস্টে
   ব্যবহৃত হয় (≥20/day ভালো, <15/day খারাপ)।

6. **Repeat market visit** = একই আউটলেট (Market Id) যদি আলাদা আলাদা তারিখে
   একাধিকবার ভিজিট হয়, সেটাকে "repeat" ধরা হয়েছে।

## 📤 প্রতিদিনের workflow

1. প্রতিদিন সেই দিনের Excel export করো (একই ২টা শীটের ফরম্যাটে —
   "SO Activity" আর "SO Attendance")
2. Dashboard link-এ যাও → sidebar-এর Admin প্যানেল → password দাও →
   ফাইল আপলোড করো
3. সাথে সাথে dashboard আপডেট হয়ে যাবে — Boss যখনই link খুলবে, নতুন ডেটাই
   দেখবে
