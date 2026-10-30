<script setup>
import { computed, ref } from 'vue'
import ToolPage from '../freemium/components/ToolPage.vue'
import CodePane from '../freemium/components/CodePane.vue'
import Segmented from '../freemium/components/ui/Segmented.vue'
import { badgeMarkdown, customBadge, generateBadges } from './badges'
const mode = ref('project')
const category = ref('github')
const type = ref('shields')
const style = ref('')
const value = ref('')
const custom = ref({
  label: '工具',
  content: '好用',
  color: '#4ea4ef',
  labelColor: '#424856',
  logo: 'github',
  logoColor: '#ffffff',
})
const result = computed(() => {
  try {
    return {
      items:
        mode.value === 'project'
          ? generateBadges(value.value, category.value, type.value, style.value)
          : [
              {
                label: custom.value.label,
                url: customBadge({ ...custom.value, style: style.value }),
              },
            ],
      error: '',
    }
  } catch (e) {
    return { items: [], error: e.message }
  }
})
</script>
<template>
  <ToolPage>
    <template #options
      ><Segmented
        v-model="mode"
        label="徽章类型"
        :options="[
          { value: 'project', label: '项目徽章' },
          { value: 'custom', label: '自定义徽章' },
        ]"
      /><label class="jay-field"
        >样式<select v-model="style" class="field">
          <option value="">默认</option>
          <option value="flat">扁平</option>
          <option v-if="type === 'badgen' && mode === 'project'" value="classic">经典</option>
          <template v-else
            ><option value="plastic">立体</option>
            <option value="flat-square">方角</option>
            <option value="for-the-badge">大号</option>
            <option value="social">社交</option></template
          >
        </select></label
      ></template
    >
    <Transition name="jay-panel" mode="out-in" @before-leave="(el) => (el.inert = true)">
      <div v-if="mode === 'project'" key="project" class="jay-panel jay-form-grid">
        <label class="jay-field"
          >项目来源<select v-model="category" class="field">
            <option value="github">GitHub</option>
            <option value="npm">npm</option>
            <option value="docker">Docker</option>
          </select></label
        >
        <label class="jay-field"
          >徽章服务<select v-model="type" class="field" @change="style = ''">
            <option value="shields">Shields</option>
            <option value="badgen">Badgen</option>
          </select></label
        >
        <label class="jay-field"
          >{{ category === 'github' ? '账号/仓库' : category === 'npm' ? '包名' : '镜像名'
          }}<input v-model="value" class="field" placeholder="例如 vuejs/core"
        /></label>
        <button
          class="btn"
          @click="
            value =
              category === 'github' ? 'vuejs/core' : category === 'npm' ? 'vue' : 'library/nginx'
          "
        >
          示例
        </button>
      </div>
      <div v-else key="custom" class="jay-panel jay-form-grid">
        <label
          v-for="(title, key) in {
            label: '左侧文字',
            content: '右侧文字',
            color: '徽章颜色',
            labelColor: '标签颜色',
            logo: 'Logo 名称',
            logoColor: 'Logo 颜色',
          }"
          :key="key"
          class="jay-field"
          >{{ title
          }}<input
            v-model="custom[key]"
            class="field"
            :type="key.toLowerCase().includes('color') ? 'color' : 'text'"
        /></label>
      </div>
    </Transition>
    <CodePane
      :model-value="badgeMarkdown(result.items)"
      :error="result.error"
      label="Markdown 引用代码"
      readonly
      download="badges.md"
    />
    <p class="jay-note">在本地生成引用代码。下方链接会打开徽章服务并发送对应的项目名或徽章文字。</p>
    <div class="jay-badge-links">
      <a
        v-for="item in result.items"
        :key="item.url"
        :href="item.url"
        target="_blank"
        rel="noopener noreferrer"
        >{{ item.label }} ↗</a
      >
    </div>
  </ToolPage>
</template>
