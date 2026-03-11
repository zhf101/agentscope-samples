import { loginApi } from "@/services/api/login";
import { message } from "@agentscope-ai/design";
import {
  SparkEmailLine,
  SparkLockLine,
  SparkUserLine,
} from "@agentscope-ai/icons";
import type { ProFormInstance } from "@ant-design/pro-components";
import {
  LoginForm,
  ProConfigProvider,
  ProFormText,
} from "@ant-design/pro-components";
import { theme } from "antd";
import { useRef } from "react";
import { useNavigate } from "react-router-dom";
import styles from "./index.module.scss";
import { useI18n } from "@/context/LanguageContext";

export const Login = () => {
  const { token } = theme.useToken();
  const formRef = useRef<ProFormInstance>();
  const urlParams = new URLSearchParams(window.location.search);
  const mode = urlParams.get("mode");
  const navigate = useNavigate();
  const { t } = useI18n();
  const onFinish = async () => {
    try {
      const values = await formRef?.current?.validateFields();
      if (mode === "register") {
        delete values?.repassword;
        const register = await loginApi.register(values);
        message.success(t("login.registerSuccess"));
        navigate("/login?mode=login");
        const { payload } = register;
        if (payload?.access_token)
          localStorage.setItem("access_token", payload?.access_token);
        if (payload?.refresh_token)
          localStorage.setItem("refresh_token", payload?.refresh_token);
        // console.log(register, "register");
      }
      if (mode === "login") {
        const login = await loginApi.login(values);
        const { payload } = login;
        if (payload?.access_token)
          localStorage.setItem("access_token", payload?.access_token);
        if (payload?.refresh_token)
          localStorage.setItem("refresh_token", payload?.refresh_token);
        navigate("/");
      }
    } catch (errorInfo: any) {
      if (mode === "login") {
        message.error(
          errorInfo?.response?.data?.detail || t("login.failed"),
        );
      }
      if (mode === "register") {
        message.error(
          errorInfo?.response?.data?.detail || t("login.registerFailed"),
        );
      }
    }
  };
  return (
    <div className={styles.container}>
      <div className={styles.logWrap}>
        <ProConfigProvider hashed={false}>
          <div style={{ backgroundColor: token.colorBgContainer }}>
            <LoginForm
              title={t("login.pageTitle")}
              formRef={formRef}
              onFinish={onFinish}
            >
              {mode === "register" && (
                <ProFormText
                  name="username"
                  fieldProps={{
                    size: "large",
                    prefix: <SparkUserLine className={"prefixIcon"} />,
                  }}
                  placeholder={t("login.usernamePlaceholder")}
                  rules={[
                    {
                      required: true,
                      message: t("login.usernameRequired"),
                    },
                  ]}
                />
              )}

              <ProFormText
                name="email"
                fieldProps={{
                  size: "large",
                  prefix: <SparkEmailLine className={"prefixIcon"} />,
                }}
                placeholder={t("login.emailPlaceholder")}
                rules={[
                  {
                    required: true,
                    message: t("login.emailRequired"),
                  },
                  {
                    pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                    message: t("login.emailInvalid"),
                  },
                ]}
              />
              <ProFormText.Password
                name="password"
                fieldProps={{
                  size: "large",
                  prefix: <SparkLockLine className={"prefixIcon"} />,
                }}
                placeholder={t("login.passwordPlaceholder")}
                rules={[
                  {
                    required: true,
                    message: t("login.passwordRequired"),
                  },
                  {
                    pattern: /^\S{2,40}$/,
                    message: t("login.passwordInvalid"),
                  },
                ]}
              />
              {mode === "register" && (
                <ProFormText.Password
                  name="repassword"
                  fieldProps={{
                    size: "large",
                    prefix: <SparkLockLine className={"prefixIcon"} />,
                  }}
                  placeholder={t("login.repasswordPlaceholder")}
                  rules={[
                    {
                      required: true,
                      message: t("login.passwordRequired"),
                    },
                    ({ getFieldValue }) => ({
                      validator(_, value) {
                        if (!value || getFieldValue("password") === value) {
                          return Promise.resolve();
                        }
                        return Promise.reject(
                          new Error(t("login.passwordMismatch")),
                        );
                      },
                    }),
                  ]}
                />
              )}
            </LoginForm>
          </div>
        </ProConfigProvider>
      </div>
    </div>
  );
};
export default Login;
