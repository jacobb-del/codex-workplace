# Expense Tracker (React)

A simple expense tracking web app built with React and Vite.

## Features

- Add both income and expense entries
- Show total balance, income, and expenses
- Filter entries by month
- Persist entries in `localStorage`
- Clean component-based structure
- Minimal modern UI

## Project structure

```text
src/
  components/
    EntryForm.jsx
    EntryList.jsx
    MonthFilter.jsx
    SummaryCard.jsx
  App.jsx
  main.jsx
  styles.css
```

## Run locally

1. Install dependencies:

   ```bash
   npm install
   ```

2. Start development server:

   ```bash
   npm run dev
   ```

3. Open the local URL shown in the terminal (typically `http://localhost:5173`).

## Build for production

```bash
npm run build
```
