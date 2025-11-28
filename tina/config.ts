import { defineConfig } from "tinacms";

// Your hosting provider likely exposes this as an environment variable
//const branch =
//  process.env.GITHUB_BRANCH ||
//  process.env.VERCEL_GIT_COMMIT_REF ||
//  process.env.HEAD ||
//  "main";
  const branch = "main";
  //const isLocal = process.env.NODE_ENV === "development";
  //const isProduction = process.env.NODE_ENV === "production";

export default defineConfig({
  branch,

  // Get this from tina.io
  clientId: process.env.TINA_PUBLIC_CLIENT_ID,
  // Get this from tina.io
  token: process.env.TINA_TOKEN,

  build: {
    outputFolder: "admin",
    publicFolder: "static",
  },
  media: {
    tina: {
      mediaRoot: "",
      publicFolder: "static",
    },
  },

  // Se añade esta opción para que TinaCMS cargue assets con la ruta correcta
  //assetsPath: isProduction ? "/waiq-full/admin/" : "/admin/",
  //assetsPath: "/waiq-full/admin/" ,

  // See docs on content modeling for more info on how to setup new content models: https://tina.io/docs/r/content-modelling-collections/
  schema: {
    collections: [
      {
        name: "article_es",
        label: "Article (ES)",
        path: "content/es/article",
        fields: [
          { type: "string", name: "title", label: "Title", isTitle: true, required: true },
          { type: "string", name: "areas", label: "Areas", list: true,
              options: ['technology', 'society', 'legal', 'ip', 'regulation', 'innovation', 'use cases', 'business', 'ethical'] },
          { type: "string", name: 'topics', label: 'Topics', component: 'list', field: {
              component: 'select',
              options: ['web3', 'ai', 'quantum']},
          },
          { type: "datetime", name: "date", label: "Date" },
          { type: "string", name: "description", label: "Description" },
          { type: "boolean", name: "draft", label: "Draft" },
          { type: "string", name: "button_url", label: "Button link" },
          { type: "string", name: "button_label", label: "Button label" },
          { type: "boolean", name: "featured", label: "Featured" },
          { type: "image", name: "image", label: "Image" },
          { type: "rich-text", name: "body", label: "Body", isBody: true }
        ],
      },
      {
        name: "article_en",
        label: "Article (EN)",
        path: "content/en/article",
        fields: [
          { type: "string", name: "title", label: "Title", isTitle: true, required: true },
          { type: "string", name: "areas", label: "Areas", list: true,
              options: ['technology', 'society', 'legal', 'ip', 'regulation', 'innovation', 'use cases', 'business', 'ethical'] },
          { type: "string", name: 'topics', label: 'Topics', component: 'list', field: {
              component: 'select',
              options: ['web3', 'ai', 'quantum']},
          },
          { type: "datetime", name: "date", label: "Date" },
          { type: "string", name: "description", label: "Description" },
          { type: "boolean", name: "draft", label: "Draft" },
          { type: "string", name: "button_url", label: "Button link" },
          { type: "string", name: "button_label", label: "Button label" },
          { type: "boolean", name: "featured", label: "Featured" },
          { type: "image", name: "image", label: "Image" },
          { type: "rich-text", name: "body", label: "Body", isBody: true }
        ],
      },
      {
        name: "banner_en",
        label: "BAnner (EN)",
        path: "content/en/banner",
        fields: [
          { type: "string", name: "title", label: "Title", isTitle: true, required: true },
          { type: "datetime", name: "date", label: "Date" },
          { type: "string", name: "description", label: "Description" },
          { type: "boolean", name: "draft", label: "Draft" },
          { type: "string", name: "h1", label: "Cabecera" },
          { type: "string", name: "style", label: "Style classes" },
          { type: "string", name: "subtitle", label: "Subtitle" },
          { type: "string", name: "button_label", label: "Button Label" },
          { type: "string", name: "button_link", label: "Button Link" },
          { type: "image", name: "image", label: "Image" },
          { type: "rich-text", name: "body", label: "Body", isBody: true }
        ],
      },
      {
        name: "banner_es",
        label: "BAnner (ES)",
        path: "content/es/banner",
        fields: [
          { type: "string", name: "title", label: "Title", isTitle: true, required: true },
          { type: "datetime", name: "date", label: "Date" },
          { type: "string", name: "description", label: "Description" },
          { type: "boolean", name: "draft", label: "Draft" },
          { type: "string", name: "h1", label: "Cabecera" },
          { type: "string", name: "style", label: "Style classes" },
          { type: "string", name: "subtitle", label: "Subtitle" },
          { type: "string", name: "button_label", label: "Button Label" },
          { type: "string", name: "button_link", label: "Button Link" },
          { type: "image", name: "image", label: "Image" },
          { type: "rich-text", name: "body", label: "Body", isBody: true }
        ],
      },
      {
        name: "picture",
        label: "Profile picture",
        path: "content/en/picture",
        fields: [
          { type: "string", name: "title", label: "Title", isTitle: true, required: true },
          { type: "datetime", name: "date", label: "Date" },
          { type: "boolean", name: "draft", label: "Draft" },
          { type: "image", name: "image", label: "Image" },
          { type: "string", name: "linkedin", label: "Linkedin URL" },
          { type: "rich-text", name: "body", label: "Body", isBody: true }
        ],
      }
    ],
  },
});
