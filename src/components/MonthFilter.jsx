export default function MonthFilter({ months, selectedMonth, onChange }) {
  return (
    <label className="month-filter">
      Month
      <select value={selectedMonth} onChange={(event) => onChange(event.target.value)}>
        <option value="all">All months</option>
        {months.map((month) => (
          <option key={month} value={month}>
            {month}
          </option>
        ))}
      </select>
    </label>
  );
}
