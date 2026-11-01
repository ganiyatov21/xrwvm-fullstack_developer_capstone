export async function api(path, options = {}) {
  const csrf = document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
  const response = await fetch('/djangoapp/' + path, {...options, headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrf || '', ...options.headers}});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'The request failed. Please try again.');
  return data;
}
