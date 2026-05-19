<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Proste pole tekstowe</title>
</head>
<body>
  <label for="inputText">Wpisz coś:</label>
  <input id="inputText" type="text" placeholder="Tutaj tekst">
  <button onclick="pokazTekst()">Pokaż</button>

  <script>
    function pokazTekst() {
      const tekst = document.getElementById('inputText').value;
      alert('Wpisano: ' + tekst);
    }
  </script>
</body>
</html>