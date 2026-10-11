import { createApp, ref } from "vue/dist/vue.esm-bundler.js";
import "./style.css";

createApp({
  setup() {
    const username = ref("");
    const password = ref("");
    const message = ref("");
    const status = ref("");
    const loading = ref(false);

    async function login() {
      loading.value = true;
      message.value = "";
      status.value = "";

      try {
        const response = await fetch("/api/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username: username.value, password: password.value }),
        });
        const result = await response.json();
        message.value = result.message;
        status.value = response.ok ? "success" : "error";
      } catch {
        message.value = "服务暂时不可用";
        status.value = "error";
      } finally {
        loading.value = false;
      }
    }

    return { username, password, message, status, loading, login };
  },
  template: `
    <main class="page-shell">
      <section class="login-card" aria-labelledby="login-title">
        <div class="brand-mark">A</div>
        <p class="eyebrow">WELCOME BACK</p>
        <h1 id="login-title">登录账户</h1>
        <p class="subtitle">请输入你的账户信息以继续</p>

        <form @submit.prevent="login">
          <label for="username">用户名</label>
          <input id="username" v-model="username" name="username" autocomplete="username" placeholder="例如：admin" />

          <label for="password">密码</label>
          <input id="password" v-model="password" name="password" type="password" autocomplete="current-password" placeholder="请输入密码" />

          <button type="submit" :disabled="loading">{{ loading ? "登录中…" : "登录" }}</button>
        </form>

        <p v-if="message" class="message" :class="status" role="alert">{{ message }}</p>
        <p class="hint">演示账号：admin / password123</p>
      </section>
    </main>
  `,
}).mount("#app");
