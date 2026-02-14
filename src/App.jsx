import { useEffect, useMemo, useState } from 'react';
import EntryForm from './components/EntryForm';
import EntryList from './components/EntryList';
import MonthFilter from './components/MonthFilter';
import SummaryCard from './components/SummaryCard';

const STORAGE_KEY = 'expense-tracker-entries-v1';

function loadStoredEntries() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export default function App() {
  const [entries, setEntries] = useState(loadStoredEntries);
  const [selectedMonth, setSelectedMonth] = useState('all');

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
  }, [entries]);

  const months = useMemo(() => {
    const uniqueMonths = new Set(entries.map((entry) => entry.date.slice(0, 7)));
    return Array.from(uniqueMonths).sort((a, b) => b.localeCompare(a));
  }, [entries]);

  const filteredEntries = useMemo(() => {
    if (selectedMonth === 'all') return entries;
    return entries.filter((entry) => entry.date.startsWith(selectedMonth));
  }, [entries, selectedMonth]);

  const totals = useMemo(() => {
    return filteredEntries.reduce(
      (acc, entry) => {
        if (entry.type === 'income') acc.income += entry.amount;
        if (entry.type === 'expense') acc.expenses += entry.amount;
        return acc;
      },
      { income: 0, expenses: 0 }
    );
  }, [filteredEntries]);

  const balance = totals.income - totals.expenses;

  function handleAddEntry(newEntry) {
    setEntries((prev) => [newEntry, ...prev].sort((a, b) => b.date.localeCompare(a.date)));
  }

  return (
    <main className="app-shell">
      <section className="panel">
        <header className="header-row">
          <div>
            <h1>Expense Tracker</h1>
            <p>Track income and expenses in one place.</p>
          </div>
          <MonthFilter
            months={months}
            selectedMonth={selectedMonth}
            onChange={setSelectedMonth}
          />
        </header>

        <SummaryCard income={totals.income} expenses={totals.expenses} balance={balance} />

        <EntryForm onAddEntry={handleAddEntry} />

        <EntryList entries={filteredEntries} />
      </section>
    </main>
  );
}
