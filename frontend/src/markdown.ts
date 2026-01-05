export const exampleMarkdown = `
\`\`\`table
option = {
  columns: [
    {
      label: 'Name',
      prop: 'name',
      width: 100,
    },
    {
      label: 'Age',
      prop: 'age',
      width: 100,
    },
    {
      label: 'City',
      prop: 'city',
      width: 100,
    },
  ],
  data: [
    {
      name: 'John',
      age: 25,
      city: 'New York',
    },
    {
      name: 'Jane',
      age: 30,
      city: 'Los Angeles',
    },
    {
      name: 'Jim',
      age: 35,
      city: 'Chicago',
    },
  ],
}
\`\`\`

\`\`\`chart
option = {
  type: 'line',
  data: [
    {
      name: 'Line 1',
      data: [1, 2, 3, 4, 5],
    },
  ],
  xAxis: {
    type: 'category',
    data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
  },
  yAxis: {
    type: 'value',
  },
}
\`\`\`

\`\`\`chart
option = {
  type: 'bar',
  data: [
    {
      name: 'Bar 1',
      data: [1, 2, 3, 4, 5],
    },
  ],
  xAxis: {
    type: 'category',
    data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
  },
  yAxis: {
    type: 'value',
  },
}
\`\`\`
`
