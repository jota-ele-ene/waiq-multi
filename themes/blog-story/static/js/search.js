
function displayResults (results, store) {
  const searchResults = document.getElementById('results')
  if (results.length) {
    let resultList = '<li></li>'
    // Iterate and build result list elements
    for (const n in results) {
      const item = store[results[n].ref]
      resultList += '<li><a href="' + item.url + '">' + item.title + '</a>'
      resultList += '<ul id="categories">'
      for (const m in item.topics) {
          resultList += '<li><h4><a href="/topics/' + item.topics[m].toLowerCase() + '">' + item.topics[m] + '</a></h4> </li>'
      }
      for (const m in item.areas) {
          resultList += '<li><h4 class="areas"><a href="/areas/' + item.areas[m].toLowerCase() + '">' + item.areas[m] + '</a></h4> </li>'
      }
      resultList += '</ul></li>'
      //resultList += '<p>' + item.content.substring(0, 150) + '...</p></li>'
    }
    searchResults.innerHTML = resultList + '<li></li>'
  } else {
    searchResults.innerHTML = 'No results found<br>Try another keywords'
  }
}


function search () {

  const query = document.getElementsByName("query")[0].value

  // Perform a search if there is a query
  if (query) {
    // Retain the search input in the form when displaying results
    document.getElementById('search-input').setAttribute('value', query)

    const idx = lunr(function () {
      this.ref('id')
      this.field('title', {
        boost: 15
      })
      this.field('topics', {
        boost: 20
      })
      this.field('areas', {
        boost: 20
      })
      this.field('content', {
        boost: 10
      })

      for (const key in window.store) {
        this.add({
          id: key,
          title: window.store[key].title,
          topics: window.store[key].topics,
          areas: window.store[key].areas,
          content: window.store[key].content
        })
      }
    })

    // Perform the search
    const results = idx.search(query)
    // Update the list with results
    displayResults(results, window.store)
  }

}
