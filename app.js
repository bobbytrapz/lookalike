// Import stylesheets

const MODES = ["show-all", "show-one", "show-two"];

const clear = mode => {
  const name = "." + mode;
  const app = document.querySelector(name);
  const clone = app.cloneNode(false);
  app.parentNode.replaceChild(clone, app);
  return document.querySelector(name);
};

const show = mode => {
  for (const other of MODES) {
    document.querySelector("." + other).classList.add("hidden");
  }
  document.querySelector("." + mode).classList.remove("hidden");
  window.scrollTo(0, 0);
};

const clearAll = () => {
  for (const mode of MODES) {
    clear(mode);
  }
};

const change = (mode, data) => {
  clearAll();
  draw(mode, data);
};

const idolProfile = (idol, should_show_similarity = true) => {
  // deconstruct
  const name = idol["name"];
  const group = idol["group"].toUpperCase();
  const image_url = idol["image_url"];

  // add object container
  const el = document.createElement("div");
  el.classList.add("idol");

  // add name
  const p = document.createElement("p");
  p.classList.add("name");
  p.innerText = `${name} (${group})`;
  el.appendChild(p);

  // add image
  const img = document.createElement("img");
  img.classList.add("face");
  img.src = image_url;
  el.appendChild(img);

  if ("similarity" in idol && should_show_similarity) {
    // add similarity
    const similarity = idol["similarity"] * 100;
    const sim = document.createElement("p");
    sim.innerText = `${similarity}`;
    sim.classList.add("similarity");
    el.appendChild(sim);
  }

  return el;
};

const showAll = data => {
  const app = clear("show-all");

  // add container
  const div = document.createElement("div");
  div.classList.add("idols");
  app.appendChild(div);

  // add faces
  for (const idol of data) {
    const el = idolProfile(idol);
    div.appendChild(el);

    // add controls
    el.querySelector("img").onclick = () => {
      const name = idol["name"];
      console.log(name);
      const data = window.DATA[name];
      if (!!data) {
        change("show-one", data);
      } else {
        console.error("idol not found:", name);
      }
    };
  }

  show("show-all");
  return data;
};

const showOne = idol => {
  const app = clear("show-one");

  // add container
  const one = document.createElement("div");
  one.classList.add("idols");
  app.appendChild(one);

  // add idol
  const idolEL = idolProfile(idol);
  idolEL.querySelector("img").onclick = () => {
    change("show-all", window.DATA);
  };
  one.appendChild(idolEL);

  const top10_h2 = document.createElement("h2");
  top10_h2.classList.add("subtitle");
  top10_h2.innerText = "Matches";
  app.appendChild(top10_h2);

  // add container
  const top10 = document.createElement("div");
  top10.classList.add("idols");
  app.appendChild(top10);

  // add top10
  const top10Matches = idol["top_10"].sort(
    (a, b) => b["similarity"] - a["similarity"]
  );
  for (const other of top10Matches) {
    const el = idolProfile(other);
    el.querySelector("img").onclick = () => {
      change("show-two", [idol, other]);
    };
    top10.appendChild(el);
  }

  const top_h2 = document.createElement("h2");
  top_h2.classList.add("subtitle");
  top_h2.innerText = "Group Matches";
  app.appendChild(top_h2);

  // add container
  const top = document.createElement("div");
  top.classList.add("idols");
  app.appendChild(top);

  // add top
  const groupMatches = Object.entries(idol["top"]).sort(
    (a, b) => b[1]["similarity"] - a[1]["similarity"]
  );
  for (const [group, gm] of groupMatches) {
    const el = idolProfile(gm);
    el.querySelector("img").onclick = () => {
      change("show-two", [idol, gm]);
    };

    top.appendChild(el);
  }

  show("show-one");
  return idol;
};

const showTwo = (a, b) => {
  const app = clear("show-two");
  console.log("a", a, "b", b);

  // add container
  const div = document.createElement("div");
  div.classList.add("idols");
  app.appendChild(div);

  let similarity = 0;
  for (const idol of [a, b]) {
    if ("similarity" in idol) {
      similarity = idol["similarity"] * 100;
      break;
    }
  }

  // add faces
  for (const idol of [a, b]) {
    const el = idolProfile(idol, false);
    div.appendChild(el);

    // add controls
    el.querySelector("img").onclick = () => {
      const name = idol["name"];
      console.log(name);
      const data = window.DATA[name];
      if (!!data) {
        change("show-one", data);
      } else {
        console.error("idol not found:", name);
      }
    };
  }

  // add similarity
  const sim = document.createElement("p");
  sim.innerText = `${similarity}`;
  sim.classList.add("similarity");
  app.appendChild(sim);

  show("show-two");
  return [a, b];
};

const draw = (mode, data) => {
  switch (mode) {
    case "show-all":
      {
        const idols = [];
        for (const [name, idol] of Object.entries(data)) {
          idols.push(idol);
        }
        data = showAll(idols);
      }
      break;
    case "show-one":
      {
        data = showOne(data);
      }
      break;
    case "show-two":
      {
        const [a, b] = data;
        data = showTwo(a, b);
      }
      break;
    default:
      console.error("invalid mode");
  }
  return data;
};

// load data
document.addEventListener("DOMContentLoaded", () => {
  fetch("/lookalike.json")
    .then(res => res.json())
    .then(data => {
      window.DATA = data;

      // initial draw
      change("show-all", window.DATA);
    });
});

// controls
document.querySelector(".title").onclick = () => {
  change("show-all", window.DATA);
};

document.querySelector(".search").addEventListener("input", ev => {
  let q = ev.target.value.toUpperCase();
  q = q
    .replace("４", "4")
    .replace("６", "6")
    .replace("８", "8");
  const found = {};
  for (const [name, idol] of Object.entries(window.DATA)) {
    const g = idol["group"].toUpperCase();
    if (name.toUpperCase().startsWith(q) || g.startsWith(q)) {
      found[name] = idol;
    }
  }
  change("show-all", found);
});
