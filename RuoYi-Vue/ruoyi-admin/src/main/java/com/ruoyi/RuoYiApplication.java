package com.ruoyi;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.jdbc.autoconfigure.DataSourceAutoConfiguration;

/**
 * 启动程序
 * 
 * @author ruoyi
 */
@SpringBootApplication(exclude = { DataSourceAutoConfiguration.class })
public class RuoYiApplication
{
    public static void main(String[] args)
    {
        // System.setProperty("spring.devtools.restart.enabled", "false");
        SpringApplication.run(RuoYiApplication.class, args);
        System.out.println("(♥◠‿◠)ﾉﾞ  GEO Prompt优化系统启动成功   ლ(´ڡ`ლ)ﾞ  \n" +
                "     ______    ______     ______      \n" +
                "    / ____/   | _____/  //  __  \\\\    \n" +
                "   | |  __    | |___   // //  \\\\ \\\\   \n" +
                "   | | |_ \\\\  |  ___| || ||    || ||  \n" +
                "   | |___| |  |______  \\\\ \\\\__// //   \n" +
                "    \\\\____//  |______|  \\\\______//    \n" +
                "                                \n" +
                "                                           ");
    }
}
